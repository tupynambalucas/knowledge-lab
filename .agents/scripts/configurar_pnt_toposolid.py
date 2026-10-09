# -*- coding: UTF-8 -*-
"""
================================================================================
AUTOMAÇÃO REVIT API / PYREVIT / REVIT MCP
REPRESENTAÇÃO DO PERFIL NATURAL DO TERRENO (PNT) EM CORTES COM TOPOSOLID
================================================================================

Objetivo:
    Configurar a representação gráfica do Perfil Natural do Terreno (PNT)
    a partir de um Sólido Topográfico (Toposolid) duplicado/clonado e demolido
    na fase de projeto. Garante que o terreno natural apareça apenas como linha
    de corte vermelha tracejada, sem massa sólida opaca, sem manchas de fundo e
    sem interferência nas vistas 3D.

Compatibilidade:
    - Autodesk Revit 2024, 2025 e 2026.
    - Execução via Revit MCP Server (ferramenta execute_revit_code).
    - Execução direta via pyRevit / RevitPythonShell / pyRevit pushbutton.

Regras Gráficas Aplicadas:
    1. Identificação do Toposolid com Fase Criada = 'Existente' e Fase Demolida = 'Projeto'.
    2. Vistas de Corte:
       - Fase da Vista = 'Projeto'.
       - Filtro de Fase com status Demolido = 'Overridden' (Com Sobreposição).
       - Sobreposição Gráfica do Elemento (OverrideGraphicSettings):
         * Linha de Corte: Vermelho (RGB 255, 0, 0), Espessura 5, Padrão Tracejado.
         * Padrões de Preenchimento (Corte e Projeção): Desativados (visibilidade desligada).
         * Transparência de Superfície: 100% (elimina qualquer sólido/sombra opaca).
       - Deslocamento do Recorte Afastado (Far Clip Offset) ajustado para 0.20 m (limita projeção de fundo).
    3. Materiais de Demolição:
       - Transparência ajustada para 100% e hachuras removidas.
    4. Vistas 3D:
       - Fase da Vista = 'Projeto'.
       - Filtro de Fase = 'Final' / 'Show Complete' (Demolidos ocultos).
"""

import sys
import traceback
from contextlib import contextmanager

# ----------------------------------------------------------------------
# 1. INICIALIZAÇÃO DE AMBIENTE E REFERÊNCIAS
# ----------------------------------------------------------------------
try:
    import clr
    import System
    clr.AddReference("RevitAPI")
    clr.AddReference("RevitAPIUI")
    import Autodesk.Revit.DB as DB

    # Detecção do Documento Ativo (pyRevit vs MCP vs Standalone)
    if "doc" not in globals():
        try:
            from pyrevit import revit
            doc = revit.doc
        except Exception:
            doc = __revit__.ActiveUIDocument.Document
except Exception as init_err:
    # No ambiente do Revit MCP, doc, DB, clr e System já estão injetados no namespace
    pass

# ----------------------------------------------------------------------
# 2. PARÂMETROS DE CONFIGURAÇÃO DO PROJETO
# ----------------------------------------------------------------------
CONFIG = {
    # Nomes ou palavras-chave das fases no projeto
    "PHASE_EXISTING_NAMES": ["existente", "existing", "exist"],
    "PHASE_PROJECT_NAMES": ["projeto", "project", "nova construção", "new construction"],

    # Filtro das vistas de corte a processar.
    # Deixe a lista com nomes para filtrar cortes específicos (ex: ["Corte Long. - Bloco 01", ...])
    # Se a lista estiver vazia [], o script processará TODOS os cortes de projeto do modelo.
    "TARGET_SECTION_NAMES": [
        "Corte Long. - Bloco 01",
        "Corte Long. - Bloco 02",
        "Corte Transversal - Vestiário"
    ],

    # Sobreposição de linha de corte do PNT
    "LINE_COLOR_RGB": (255, 0, 0),  # Vermelho
    "LINE_WEIGHT": 5,               # Espessura entre 4 e 5
    "LINE_PATTERN_NAME": "PNT Tracejado",

    # Profundidade do plano de corte afastado em metros (Far Clip Offset)
    "FAR_CLIP_OFFSET_METERS": 0.20,

    # Nomes dos filtros de fase
    "SECTION_PHASE_FILTER_NAME": "PNT - Demolição Sobreposta",
    "3D_PHASE_FILTER_NAMES": ["exibir completo", "show complete", "final", "concluído", "concluido"]
}

# ----------------------------------------------------------------------
# 3. GERENCIADOR DE TRANSAÇÕES RESILIENTE (MCP + PYREVIT DUAL-MODE)
# ----------------------------------------------------------------------
@contextmanager
def revit_transaction(document, transaction_name="Configurar PNT Toposolid"):
    """
    Controla o ciclo de vida da transação da Revit API de forma compatível
    tanto com o servidor Revit MCP (que já encapsula o código numa transação)
    quanto com pyRevit/RPS (que exige abertura explícita de DB.Transaction).
    """
    if document.IsModifiable:
        # Já está dentro de uma transação aberta pelo Revit MCP
        yield None
    else:
        # Execução externa (pyRevit pushbutton, terminal Python, etc.)
        t = DB.Transaction(document, transaction_name)
        t.Start()
        try:
            yield t
            t.Commit()
        except Exception:
            if t.HasStarted() and not t.HasEnded():
                t.RollBack()
            raise

# ----------------------------------------------------------------------
# 4. FUNÇÕES UTILITÁRIAS E DE BUSCA
# ----------------------------------------------------------------------
def log(msg):
    """Gera saída formatada capturada tanto no console pyRevit quanto no MCP."""
    print("[PNT-SETUP] " + str(msg))

def meters_to_feet(meters):
    """Converte metros para a unidade interna da Revit API (pés decimais)."""
    return float(meters) / 0.3048

def find_phase(document, search_keywords):
    """Localiza uma fase no documento a partir de palavras-chave."""
    for phase in document.Phases:
        phase_name = phase.Name.strip().lower()
        for kw in search_keywords:
            if kw.lower() in phase_name:
                return phase
    return None

def get_or_create_line_pattern(document, pattern_name):
    """
    Localiza um padrão de linha tracejado existente ou cria um novo com traço de 4mm e espaço de 2mm.
    """
    # 1. Busca por padrão existente
    collector = DB.FilteredElementCollector(document).OfClass(DB.LinePatternElement)
    for lpe in collector.ToElements():
        name_lower = lpe.Name.lower()
        if pattern_name.lower() in name_lower or "tracej" in name_lower or "dash" in name_lower:
            return lpe

    # 2. Criação de padrão customizado se não encontrado
    try:
        from System.Collections.Generic import List
        segments = List[DB.LinePatternSegment]()
        # 4mm traço = 4.0 / 304.8 pés; 2mm espaço = 2.0 / 304.8 pés
        segments.Add(DB.LinePatternSegment(DB.LinePatternSegmentType.Dash, 4.0 / 304.8))
        segments.Add(DB.LinePatternSegment(DB.LinePatternSegmentType.Space, 2.0 / 304.8))

        lp = DB.LinePattern(pattern_name)
        lp.SetSegments(segments)
        created_elem = DB.LinePatternElement.Create(document, lp)
        log("Padrão de linha criado: '{}'".format(pattern_name))
        return created_elem
    except Exception as err:
        log("Aviso: Não foi possível criar padrão de linha: {}. Usando padrão contínuo.".format(err))
        return None

def get_or_create_section_phase_filter(document, filter_name):
    """
    Obtém ou cria um filtro de fase específico para cortes arquitetônicos onde:
    - Novo = Por Categoria (ShowByCategory)
    - Existente = Por Categoria (ShowByCategory)
    - Demolido = Com Sobreposição (ShowOverriden) -> essencial para o PNT
    - Temporário = Não Exibido (DontShow)
    """
    collector = DB.FilteredElementCollector(document).OfClass(DB.PhaseFilter)
    for pf in collector.ToElements():
        if pf.Name.strip().lower() == filter_name.lower():
            # Configura o filtro existente para as regras exatas
            pf.SetPhaseStatusPresentation(DB.ElementOnPhaseStatus.New, DB.PhaseStatusPresentation.ShowByCategory)
            pf.SetPhaseStatusPresentation(DB.ElementOnPhaseStatus.Existing, DB.PhaseStatusPresentation.ShowByCategory)
            pf.SetPhaseStatusPresentation(DB.ElementOnPhaseStatus.Demolished, DB.PhaseStatusPresentation.ShowOverriden)
            pf.SetPhaseStatusPresentation(DB.ElementOnPhaseStatus.Temporary, DB.PhaseStatusPresentation.DontShow)
            return pf

    # Criação de novo filtro caso não exista
    try:
        new_filter = DB.PhaseFilter.Create(document, filter_name)
        new_filter.SetPhaseStatusPresentation(DB.ElementOnPhaseStatus.New, DB.PhaseStatusPresentation.ShowByCategory)
        new_filter.SetPhaseStatusPresentation(DB.ElementOnPhaseStatus.Existing, DB.PhaseStatusPresentation.ShowByCategory)
        new_filter.SetPhaseStatusPresentation(DB.ElementOnPhaseStatus.Demolished, DB.PhaseStatusPresentation.ShowOverriden)
        new_filter.SetPhaseStatusPresentation(DB.ElementOnPhaseStatus.Temporary, DB.PhaseStatusPresentation.DontShow)
        log("Filtro de fase criado com sucesso: '{}'".format(filter_name))
        return new_filter
    except Exception as err:
        log("Erro ao criar filtro de fase: {}. Buscando filtro alternativo.".format(err))
        # Fallback: procurar qualquer filtro existente onde Demolished seja Overridden
        for pf in collector.ToElements():
            if pf.GetPhaseStatusPresentation(DB.ElementOnPhaseStatus.Demolished) == DB.PhaseStatusPresentation.ShowOverriden:
                return pf
        return None

def get_complete_phase_filter(document, search_keywords):
    """
    Localiza o filtro de fase 'Final' / 'Show Complete', onde Demolidos NÃO são exibidos (DontShow).
    """
    collector = DB.FilteredElementCollector(document).OfClass(DB.PhaseFilter)
    filters = list(collector.ToElements())

    # 1. Busca por nome
    for pf in filters:
        name_lower = pf.Name.lower()
        for kw in search_keywords:
            if kw in name_lower:
                return pf

    # 2. Busca funcional: Demolished == DontShow e New == ShowByCategory
    for pf in filters:
        is_demo_hidden = (pf.GetPhaseStatusPresentation(DB.ElementOnPhaseStatus.Demolished) == DB.PhaseStatusPresentation.DontShow)
        is_new_shown = (pf.GetPhaseStatusPresentation(DB.ElementOnPhaseStatus.New) == DB.PhaseStatusPresentation.ShowByCategory)
        if is_demo_hidden and is_new_shown:
            return pf

    return None

def sanitize_demolished_materials(document):
    """
    Remove hachuras e torna transparentes quaisquer materiais do projeto associados
    à fase de demolição (ex: 'Fase - Demolida' ou 'Phase - Demolished'), evitando massas sólidas.
    """
    materials = DB.FilteredElementCollector(document).OfClass(DB.Material).ToElements()
    adjusted_count = 0

    for mat in materials:
        mat_name = mat.Name.lower()
        if "demoli" in mat_name or "demolish" in mat_name:
            try:
                # Transparência total para modos sombreados
                mat.Transparency = 100
                # Desativa hachuras de superfície e corte
                mat.CutForegroundPatternId = DB.ElementId.InvalidElementId
                mat.CutBackgroundPatternId = DB.ElementId.InvalidElementId
                mat.SurfaceForegroundPatternId = DB.ElementId.InvalidElementId
                mat.SurfaceBackgroundPatternId = DB.ElementId.InvalidElementId
                adjusted_count += 1
                log("Material de demolição ajustado para 100% transparente: '{}'".format(mat.Name))
            except Exception as e:
                log("Aviso ao ajustar material '{}': {}".format(mat.Name, e))

    return adjusted_count

# ----------------------------------------------------------------------
# 5. EXECUÇÃO PRINCIPAL DO PROCEDIMENTO
# ----------------------------------------------------------------------
def run_pnt_automation():
    """Executa a rotina completa de configuração do PNT e das vistas."""
    log("Iniciando rotina de padronização do Perfil Natural do Terreno (PNT)...")

    results = {
        "pnt_toposolids_found": 0,
        "sections_configured": 0,
        "views_3d_configured": 0,
        "materials_cleaned": 0,
        "errors": []
    }

    with revit_transaction(doc, "Padronização do Perfil Natural do Terreno (PNT)"):
        # --------------------------------------------------------------
        # ETAPA 1: MAPEAMENTO DAS FASES DO PROJETO
        # --------------------------------------------------------------
        phase_existing = find_phase(doc, CONFIG["PHASE_EXISTING_NAMES"])
        phase_project = find_phase(doc, CONFIG["PHASE_PROJECT_NAMES"])

        if not phase_existing:
            raise ValueError("Fase 'Existente' não foi encontrada no projeto. Verifique o gerenciamento de fases.")
        if not phase_project:
            raise ValueError("Fase 'Projeto' não foi encontrada no projeto. Verifique o gerenciamento de fases.")

        log("Fase 'Existente' identificada: ID {} ('{}')".format(phase_existing.Id, phase_existing.Name))
        log("Fase 'Projeto' identificada: ID {} ('{}')".format(phase_project.Id, phase_project.Name))

        # --------------------------------------------------------------
        # ETAPA 2: IDENTIFICAÇÃO DO TOPOSOLID DO TERRENO NATURAL (PNT)
        # --------------------------------------------------------------
        toposolids = (
            DB.FilteredElementCollector(doc)
            .OfCategory(DB.BuiltInCategory.OST_Toposolid)
            .WhereElementIsNotElementType()
            .ToElements()
        )

        pnt_solids = []
        for ts in toposolids:
            param_created = ts.get_Parameter(DB.BuiltInParameter.PHASE_CREATED)
            param_demolished = ts.get_Parameter(DB.BuiltInParameter.PHASE_DEMOLISHED)

            created_id = param_created.AsElementId() if param_created else DB.ElementId.InvalidElementId
            demo_id = param_demolished.AsElementId() if param_demolished else DB.ElementId.InvalidElementId

            if created_id == phase_existing.Id and demo_id == phase_project.Id:
                pnt_solids.append(ts)
                type_name = getattr(doc.GetElement(ts.GetTypeId()), "Name", "Toposolid")
                log("Toposolid PNT identificado: ID {} (Tipo: '{}')".format(ts.Id, type_name))

        if not pnt_solids:
            log("AVISO: Nenhum Toposolid com Fase Criada='Existente' e Fase Demolida='Projeto' foi encontrado.")
            log("Verifique se o sólido duplicado teve seus parâmetros de fase preenchidos corretamente.")
            return results

        results["pnt_toposolids_found"] = len(pnt_solids)

        # --------------------------------------------------------------
        # ETAPA 3: PREPARAÇÃO DOS RECURSOS GRÁFICOS E MATERIAIS
        # --------------------------------------------------------------
        # Padrão de linha tracejado
        dashed_pattern = get_or_create_line_pattern(doc, CONFIG["LINE_PATTERN_NAME"])

        # Filtro de fase para cortes
        section_phase_filter = get_or_create_section_phase_filter(doc, CONFIG["SECTION_PHASE_FILTER_NAME"])
        if not section_phase_filter:
            raise RuntimeError("Não foi possível configurar um Filtro de Fase adequado para os cortes.")

        # Limpeza preventiva de materiais de demolição
        results["materials_cleaned"] = sanitize_demolished_materials(doc)

        # Configuração do OverrideGraphicSettings para o PNT
        ogs_pnt = DB.OverrideGraphicSettings()
        color_red = DB.Color(CONFIG["LINE_COLOR_RGB"][0], CONFIG["LINE_COLOR_RGB"][1], CONFIG["LINE_COLOR_RGB"][2])

        # Linha de corte
        ogs_pnt.SetCutLineColor(color_red)
        ogs_pnt.SetCutLineWeight(CONFIG["LINE_WEIGHT"])
        if dashed_pattern:
            ogs_pnt.SetCutLinePatternId(dashed_pattern.Id)

        # Hachuras e padrões desligados
        ogs_pnt.SetCutForegroundPatternVisible(False)
        ogs_pnt.SetCutBackgroundPatternVisible(False)
        ogs_pnt.SetSurfaceForegroundPatternVisible(False)
        ogs_pnt.SetSurfaceBackgroundPatternVisible(False)

        # Transparência 100% da superfície: evita corpo branco e blocos opacos
        ogs_pnt.SetSurfaceTransparency(100)

        # --------------------------------------------------------------
        # ETAPA 4: CONFIGURAÇÃO DAS VISTAS DE CORTE
        # --------------------------------------------------------------
        views_collector = (
            DB.FilteredElementCollector(doc)
            .OfClass(DB.ViewSection)
            .WhereElementIsNotElementType()
            .ToElements()
        )

        far_clip_feet = meters_to_feet(CONFIG["FAR_CLIP_OFFSET_METERS"])
        toposolid_cat_id = DB.ElementId(DB.BuiltInCategory.OST_Toposolid)

        target_names = CONFIG["TARGET_SECTION_NAMES"]

        for view in views_collector:
            # Ignora modelos de vista (View Templates) na iteração principal
            if view.IsTemplate:
                continue

            view_name = view.Name.strip()

            # Filtragem por nomes especificados (se houver alvos definidos)
            if target_names:
                matches = any(t.lower() in view_name.lower() for t in target_names)
                if not matches:
                    continue

            log("--- Configurando Corte: '{}' (ID {}) ---".format(view_name, view.Id))

            # Alerta sobre View Template ativo
            if view.ViewTemplateId != DB.ElementId.InvalidElementId:
                vt = doc.GetElement(view.ViewTemplateId)
                log("  Aviso: Vista vinculada ao Template '{}'. Propriedades controladas podem requerer ajuste no template.".format(vt.Name))

            # 1. Definir Fase da Vista como "Projeto"
            p_phase = view.get_Parameter(DB.BuiltInParameter.VIEW_PHASE)
            if p_phase and not p_phase.IsReadOnly:
                p_phase.Set(phase_project.Id)
                log("  Fase da vista ajustada para 'Projeto'.")

            # 2. Aplicar Filtro de Fase com Sobreposição
            p_pfilter = view.get_Parameter(DB.BuiltInParameter.VIEW_PHASE_FILTER)
            if p_pfilter and not p_pfilter.IsReadOnly:
                p_pfilter.Set(section_phase_filter.Id)
                log("  Filtro de fase ajustado para '{}'.".format(section_phase_filter.Name))

            # 3. Ajustar Recorte Afastado (Far Clip Active + Offset = 0.20m)
            p_clip_active = view.get_Parameter(DB.BuiltInParameter.VIEWER_BOUND_ACTIVE_FAR)
            if p_clip_active and not p_clip_active.IsReadOnly:
                p_clip_active.Set(1)  # 1 = Recorte ativo
                log("  Recorte afastado ativado (Far Clip Active).")

            p_clip_offset = view.get_Parameter(DB.BuiltInParameter.VIEWER_BOUND_OFFSET_FAR)
            if p_clip_offset and not p_clip_offset.IsReadOnly:
                p_clip_offset.Set(far_clip_feet)
                log("  Deslocamento do recorte afastado ajustado para {:.2f} m.".format(CONFIG["FAR_CLIP_OFFSET_METERS"]))

            # 4. Assegurar que a categoria Toposolid esteja visível
            if view.CanCategoryBeHidden(toposolid_cat_id) and view.GetCategoryHidden(toposolid_cat_id):
                view.SetCategoryHidden(toposolid_cat_id, False)
                log("  Categoria Sólido Topográfico reexibida na vista.")

            # 5. Aplicar Sobreposição Gráfica direta em cada Toposolid PNT
            from System.Collections.Generic import List
            for pnt in pnt_solids:
                if pnt.IsHidden(view):
                    ids_to_unhide = List[DB.ElementId]()
                    ids_to_unhide.Add(pnt.Id)
                    view.UnhideElements(ids_to_unhide)
                    log("  Elemento Toposolid {} desocultado na vista.".format(pnt.Id))

                view.SetElementOverrides(pnt.Id, ogs_pnt)
                log("  Sobreposição gráfica aplicada ao Toposolid {} (Linha vermelha tracejada, sem sólidos).".format(pnt.Id))

            results["sections_configured"] += 1

        # --------------------------------------------------------------
        # ETAPA 5: CONFIGURAÇÃO DAS VISTAS 3D (OCULTAÇÃO DO PNT CLONE)
        # --------------------------------------------------------------
        complete_filter = get_complete_phase_filter(doc, CONFIG["3D_PHASE_FILTER_NAMES"])
        if not complete_filter:
            log("Aviso: Filtro 'Show Complete' / 'Final' não localizado. Criando filtro padrão...")
            try:
                complete_filter = DB.PhaseFilter.Create(doc, "Exibir Completo (Padrão 3D)")
                complete_filter.SetPhaseStatusPresentation(DB.ElementOnPhaseStatus.New, DB.PhaseStatusPresentation.ShowByCategory)
                complete_filter.SetPhaseStatusPresentation(DB.ElementOnPhaseStatus.Existing, DB.PhaseStatusPresentation.ShowByCategory)
                complete_filter.SetPhaseStatusPresentation(DB.ElementOnPhaseStatus.Demolished, DB.PhaseStatusPresentation.DontShow)
                complete_filter.SetPhaseStatusPresentation(DB.ElementOnPhaseStatus.Temporary, DB.PhaseStatusPresentation.DontShow)
            except Exception as e:
                log("Erro ao criar filtro 3D: {}".format(e))

        if complete_filter:
            views_3d = (
                DB.FilteredElementCollector(doc)
                .OfClass(DB.View3D)
                .WhereElementIsNotElementType()
                .ToElements()
            )

            for v3d in views_3d:
                if v3d.IsTemplate:
                    continue

                p_phase_3d = v3d.get_Parameter(DB.BuiltInParameter.VIEW_PHASE)
                if p_phase_3d and not p_phase_3d.IsReadOnly:
                    p_phase_3d.Set(phase_project.Id)

                p_pfilter_3d = v3d.get_Parameter(DB.BuiltInParameter.VIEW_PHASE_FILTER)
                if p_pfilter_3d and not p_pfilter_3d.IsReadOnly:
                    p_pfilter_3d.Set(complete_filter.Id)
                    results["views_3d_configured"] += 1

            log("Vistas 3D configuradas com Filtro '{}' (Toposolid PNT 100% invisível no 3D).".format(complete_filter.Name))

    # ------------------------------------------------------------------
    # RELATÓRIO FINAL
    # ------------------------------------------------------------------
    log("=======================================================")
    log("PROCESSO CONCLUÍDO COM SUCESSO!")
    log("- Toposolids PNT identificados: {}".format(results["pnt_toposolids_found"]))
    log("- Vistas de corte configuradas: {}".format(results["sections_configured"]))
    log("- Vistas 3D atualizadas: {}".format(results["views_3d_configured"]))
    log("- Materiais de demolição saneados: {}".format(results["materials_cleaned"]))
    log("=======================================================")
    return results

# ----------------------------------------------------------------------
# EXECUÇÃO DO SCRIPT
# ----------------------------------------------------------------------
if __name__ == "__main__" or "doc" in globals():
    try:
        run_pnt_automation()
    except Exception as general_err:
        log("FALHA NA EXECUÇÃO: {}".format(general_err))
        log(traceback.format_exc())
