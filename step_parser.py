"""
STEP File Parser and Assembly Analyzer
Parses ISO 10303-21 (STEP) files and extracts the assembly structure.
"""
import re
from collections import defaultdict


def parse_step_file(filepath):
    """Parse a STEP file into header, entities dict, and trailer."""
    header_lines = []
    trailer_lines = []
    entities = {}  # id -> raw_value (string after '=', without trailing ';')
    
    in_data = False
    in_header = True
    buffer = ''
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.rstrip('\r\n')
            
            if in_header:
                header_lines.append(line)
                if line.strip() == 'DATA;':
                    in_data = True
                    in_header = False
                continue
            
            stripped = line.strip()
            if stripped == 'ENDSEC;' or stripped == 'END-ISO-10303-21;':
                # Flush buffer
                if buffer:
                    _store_entity(buffer, entities)
                    buffer = ''
                trailer_lines.append(line)
                in_data = False
                continue
            
            if not in_data:
                trailer_lines.append(line)
                continue
            
            # Accumulate multi-line entities
            buffer += line.strip()
            if buffer.endswith(';'):
                _store_entity(buffer, entities)
                buffer = ''
    
    return header_lines, entities, trailer_lines


def _store_entity(text, entities):
    """Parse '#ID=VALUE;' and store in entities dict."""
    m = re.match(r'^#(\d+)\s*=\s*(.+);$', text)
    if m:
        eid = int(m.group(1))
        entities[eid] = m.group(2)


def get_entity_type(raw_value):
    """Extract the primary type name from an entity value string."""
    # Handle complex entities like (TYPE1(...)TYPE2(...))
    if raw_value.startswith('('):
        m = re.match(r'\(\s*([A-Z_]+)', raw_value)
    else:
        m = re.match(r'([A-Z_]+)', raw_value)
    return m.group(1) if m else None


def extract_refs(raw_value):
    """Extract all #N entity references from a value string."""
    return [int(x) for x in re.findall(r'#(\d+)', raw_value)]


def find_entities_by_type(entities, type_name):
    """Find all entity IDs of a given type."""
    result = {}
    for eid, val in entities.items():
        if type_name in val:
            # Check primary type
            if val.startswith(type_name + '('):
                result[eid] = val
            # Check complex entity types
            elif val.startswith('(') and type_name + '(' in val:
                result[eid] = val
    return result


def extract_product_name(raw_value):
    """Extract the name from a PRODUCT(...) entity."""
    m = re.match(r"PRODUCT\('([^']*)'", raw_value)
    return m.group(1) if m else None


def extract_cartesian_coords(raw_value):
    """Extract (x,y,z) from a CARTESIAN_POINT entity."""
    m = re.search(r'CARTESIAN_POINT\([^,]*,\(([^)]+)\)', raw_value)
    if m:
        return [float(x.strip()) for x in m.group(1).split(',')]
    return None


def build_reference_graph(entities):
    """Build forward and reverse reference graphs."""
    forward = defaultdict(set)   # entity -> entities it references
    reverse = defaultdict(set)   # entity -> entities that reference it
    
    for eid, val in entities.items():
        refs = extract_refs(val)
        for ref in refs:
            if ref in entities and ref != eid:
                forward[eid].add(ref)
                reverse[ref].add(eid)
    
    return dict(forward), dict(reverse)


def find_nauos(entities):
    """Find all NEXT_ASSEMBLY_USAGE_OCCURRENCE entities."""
    nauos = {}
    for eid, val in entities.items():
        if 'NEXT_ASSEMBLY_USAGE_OCCURRENCE' not in val:
            continue
        m = re.match(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('([^']*)'[^#]*#(\d+),#(\d+)", val)
        if m:
            nauos[eid] = {
                'name': m.group(1),
                'parent_pd': int(m.group(2)),
                'child_pd': int(m.group(3)),
            }
    return nauos


def find_product_defs(entities):
    """Find all PRODUCT_DEFINITION entities."""
    pds = {}
    for eid, val in entities.items():
        if val.startswith("PRODUCT_DEFINITION("):
            m = re.match(r"PRODUCT_DEFINITION\('([^']*)'", val)
            if m:
                pds[eid] = {'name': m.group(1), 'refs': extract_refs(val)}
    return pds


def collect_subtree(start_id, forward_refs, exclude=None):
    """BFS/DFS to collect all entities reachable from start_id via forward references."""
    visited = set()
    stack = [start_id]
    while stack:
        eid = stack.pop()
        if eid in visited:
            continue
        if exclude and eid in exclude:
            continue
        visited.add(eid)
        for ref in forward_refs.get(eid, []):
            if ref not in visited:
                stack.append(ref)
    return visited


def find_cdsr_transform(nauo_id, entities, forward_refs, reverse_refs):
    """
    Given a NAUO, find the CARTESIAN_POINT that defines its placement.
    Chain: NAUO -> PD_SHAPE -> CDSR -> REP_REL_WITH_TRANSFORM -> ITEM_DEF_TRANSFORM -> AXIS2_PLACEMENT_3D -> CARTESIAN_POINT
    """
    # Find PD_SHAPE that references this NAUO
    pd_shape_id = None
    for ref_id in reverse_refs.get(nauo_id, []):
        val = entities.get(ref_id, '')
        if 'PRODUCT_DEFINITION_SHAPE' in val:
            pd_shape_id = ref_id
            break
    if not pd_shape_id:
        return None, None
    
    # Find CDSR that references this PD_SHAPE
    for ref_id in reverse_refs.get(pd_shape_id, []):
        val = entities.get(ref_id, '')
        if 'CONTEXT_DEPENDENT_SHAPE_REPRESENTATION' in val:
            # Get the REP_REL reference
            refs = extract_refs(val)
            if len(refs) >= 1:
                rep_rel_id = refs[0]
                rep_rel_val = entities.get(rep_rel_id, '')
                # Get ITEM_DEFINED_TRANSFORMATION reference
                m = re.search(r'REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION\(#(\d+)\)', rep_rel_val)
                if m:
                    idt_id = int(m.group(1))
                    idt_val = entities.get(idt_id, '')
                    # Get target AXIS2_PLACEMENT_3D
                    idt_refs = extract_refs(idt_val)
                    if len(idt_refs) >= 2:
                        target_ax_id = idt_refs[1]
                        ax_val = entities.get(target_ax_id, '')
                        ax_refs = extract_refs(ax_val)
                        if ax_refs:
                            point_id = ax_refs[0]
                            coords = extract_cartesian_coords(entities.get(point_id, ''))
                            return point_id, coords
    return None, None
