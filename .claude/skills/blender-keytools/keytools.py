"""keytools - compact Blender 5.2 helpers (checks + repeated actions).

Usage inside Blender:  import keytools as kt; result = {"r": kt.check_all()}
Every function returns a short text report. Checks never modify the file.
Selection argument `sel` everywhere:
  None -> all visible objects | "selected" | object name | collection name
  | glob pattern ("Wall*") | list of any of these.
"""
import bpy, bmesh, fnmatch, os, re, math
import numpy as np
VERSION = "1.2"
from mathutils import Vector, Matrix, Euler, Quaternion
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

TOL = 0.001          # 1 mm: contact / z-fight distance
_UP, _DOWN = Vector((0, 0, 1)), Vector((0, 0, -1))


# ---------------------------------------------------------------- helpers
def _n(x):
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _v(v):
    return "(" + ", ".join(_n(x) for x in v) + ")"


def objs(sel=None, types=("MESH",)):
    """Resolve a selection to a list of objects (see module doc)."""
    vl = bpy.context.view_layer
    vl.update()
    if sel is None:
        cand = [o for o in vl.objects if o and o.visible_get()]
    elif isinstance(sel, bpy.types.Object):
        cand = [sel]
    elif isinstance(sel, str):
        if sel == "selected":
            cand = [o for o in vl.objects if o.select_get()]
        elif sel in bpy.data.objects:
            cand = [bpy.data.objects[sel]]
        elif sel in bpy.data.collections:
            cand = list(bpy.data.collections[sel].all_objects)
        else:
            cand = [o for o in vl.objects if fnmatch.fnmatchcase(o.name, sel)]
    else:
        cand = [o for s in sel for o in objs(s, None)]
    out, seen = [], set()
    for o in cand:
        if (types is None or o.type in types) and o.name not in seen:
            seen.add(o.name)
            out.append(o)
    return out


def _dg():
    bpy.context.view_layer.update()
    return bpy.context.evaluated_depsgraph_get()


class _Geo:
    """Evaluated (modifiers applied) world-space mesh + BVH + bbox."""
    def __init__(self, o, dg):
        self.o, self.name = o, o.name
        bm = bmesh.new()
        bm.from_object(o, dg)
        bm.transform(o.matrix_world)
        bm.normal_update()
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        self.bm = bm
        self.bvh = BVHTree.FromBMesh(bm)
        co = [v.co for v in bm.verts] or [o.matrix_world.translation]
        self.mn = Vector([min(c[i] for c in co) for i in range(3)])
        self.mx = Vector([max(c[i] for c in co) for i in range(3)])

    def near(self, other, tol=TOL, axes=3):
        return all(self.mn[i] - tol <= other.mx[i] and other.mn[i] - tol <= self.mx[i]
                   for i in range(axes))

    def free(self):
        self.bm.free()


def _geos(sel):
    dg = _dg()
    gs = [_Geo(o, dg) for o in objs(sel)]
    return [g for g in gs if len(g.bm.verts)]


def _touch(a, b, tol):
    if a.bvh.overlap(b.bvh):
        return True
    for x, y in ((a, b), (b, a)):
        for v in x.bm.verts:
            c = v.co
            if (y.mn.x - tol <= c.x <= y.mx.x + tol and y.mn.y - tol <= c.y <= y.mx.y + tol
                    and y.mn.z - tol <= c.z <= y.mx.z + tol):
                if y.bvh.find_nearest(c, tol)[0] is not None:
                    return True
    return False


def _origin_label(o):
    if o.type != "MESH" or not len(o.data.vertices):
        return "-"
    co = [v.co for v in o.data.vertices]
    lab = []
    for i, ax in enumerate("xyz"):
        mn, mx = min(c[i] for c in co), max(c[i] for c in co)
        if mx - mn < 1e-6:
            lab.append(f"{ax}:flat" if abs(mn) < 1e-4 else f"{ax}:off{_n(-mn)}")
            continue
        f = -mn / (mx - mn)
        lab.append(f"{ax}:" + ("min" if abs(f) < .02 else "mid" if abs(f - .5) < .02
                               else "max" if abs(f - 1) < .02 else _n(f)))
    return " ".join(lab)


def _mod_ident(mod, input_name):
    for it in mod.node_group.interface.items_tree:
        if getattr(it, "in_out", "") == "INPUT" and it.name == input_name:
            return it.identifier
    raise KeyError(f"no input '{input_name}' in {mod.node_group.name}")


def _in_get(mod, ident):
    """GN modifier input value (5.x: mod.properties.inputs.<id>.value; older: mod[id])."""
    if hasattr(mod, "properties"):
        return getattr(mod.properties.inputs, ident).value
    return mod[ident]


def _in_set(mod, ident, value):
    if hasattr(mod, "properties"):
        getattr(mod.properties.inputs, ident).value = value
    else:
        mod[ident] = value


def _gn_mod(o, modifier=None):
    for m in o.modifiers:
        if m.type == "NODES" and m.node_group and (modifier is None or m.name == modifier):
            return m
    raise KeyError(f"{o.name}: no Geometry Nodes modifier {modifier or ''}")


# ---------------------------------------------------------------- reports
def report(sel=None, maxn=60):
    """One line per object: tris, size, location, origin position in bbox, flags."""
    lines = []
    for o in objs(sel, None)[:maxn]:
        if o.type != "MESH":
            lines.append(f"{o.name} [{o.type}] loc{_v(o.matrix_world.translation)}"
                         + (f" parent={o.parent.name}" if o.parent else ""))
            continue
        me = o.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        fl = []
        s = o.scale
        if any(abs(x - 1) > 1e-4 for x in s):
            fl.append(f"scale{_v(s)}" + ("NEG" if o.matrix_world.determinant() < 0 else ""))
        if any(abs(x) > 1e-4 for x in o.rotation_euler):
            fl.append(f"rot{_v([round(x * 57.2958, 1) for x in o.rotation_euler])}deg")
        if me.users > 1:
            fl.append(f"shared:{me.name}x{me.users}")
        mods = ",".join(m.name for m in o.modifiers)
        mats = ",".join(s.material.name for s in o.material_slots if s.material)
        lines.append(f"{o.name} tris={tris} dim{_v(o.dimensions)} loc{_v(o.matrix_world.translation)}"
                     f" origin[{_origin_label(o)}]" + (" " + " ".join(fl) if fl else "")
                     + (f" mods={mods}" if mods else "") + (f" mats={mats}" if mats else "")
                     + (f" parent={o.parent.name}" if o.parent else ""))
    return "\n".join(lines) or "no objects"


def pivot(sel):
    """Where the origin sits inside each object's own bbox (min/mid/max per axis)."""
    return "\n".join(f"{o.name}: origin[{_origin_label(o)}] world{_v(o.matrix_world.translation)}"
                     for o in objs(sel))


# ---------------------------------------------------------------- checks
def check_transforms(sel=None):
    out = []
    for o in objs(sel):
        if any(abs(x - 1) > 1e-4 for x in o.scale):
            out.append(f"{o.name}: unapplied scale {_v(o.scale)}")
        if o.matrix_world.determinant() < 0:
            out.append(f"{o.name}: NEGATIVE scale (normals flip in Unity)")
    return "\n".join(out)


def check_mesh(sel=None, merge=1e-4):
    """Garbage geometry in the base mesh: loose, doubles, interior/duplicate faces,
    flipped neighbours, inside-out closed meshes, zero-area faces."""
    out = []
    for o in objs(sel):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.verts.index_update()
        iss = []
        lv = sum(1 for v in bm.verts if not v.link_edges)
        le = sum(1 for e in bm.edges if not e.link_faces)
        multi = sum(1 for e in bm.edges if len(e.link_faces) > 2)
        bound = sum(1 for e in bm.edges if len(e.link_faces) == 1)
        inner = sum(1 for f in bm.faces if all(len(e.link_faces) > 2 for e in f.edges))
        zf = sum(1 for f in bm.faces if f.calc_area() < 1e-10)
        flip = 0
        for e in bm.edges:
            if len(e.link_loops) == 2 and e.link_loops[0].vert == e.link_loops[1].vert:
                flip += 1
        keys = [frozenset(v.index for v in f.verts) for f in bm.faces]
        dupf = len(keys) - len(set(keys))
        kd = KDTree(len(bm.verts))
        for v in bm.verts:
            kd.insert(v.co, v.index)
        kd.balance()
        dbl = sum(1 for v in bm.verts
                  for _, i, _ in kd.find_range(v.co, merge) if i > v.index)
        if lv: iss.append(f"loose verts {lv}")
        if le: iss.append(f"loose edges {le}")
        if dbl: iss.append(f"double verts {dbl}")
        if dupf: iss.append(f"duplicate faces {dupf}")
        if inner: iss.append(f"interior faces {inner}")
        if multi: iss.append(f"edges with >2 faces {multi}")
        if flip: iss.append(f"inconsistent normals on {flip} edges")
        if zf: iss.append(f"zero-area faces {zf}")
        if bm.faces and bound == 0 and multi == 0 and not flip:
            vol = 0.0
            for f in bm.faces:
                v0 = f.verts[0].co
                for i in range(1, len(f.verts) - 1):
                    vol += v0.dot(f.verts[i].co.cross(f.verts[i + 1].co))
            if vol * o.matrix_world.determinant() < 0:
                iss.append("closed mesh is INSIDE-OUT (normals point in)")
        bm.free()
        if iss:
            out.append(f"{o.name}: " + ", ".join(iss))
    return "\n".join(out)


def check_floating(sel=None, ground=0.0, tol=TOL, anchors=(), ignore=()):
    """Objects not connected (by contact chain) to the ground plane or to `anchors`."""
    gs = [g for g in _geos(sel) if g.name not in ignore]
    names = [g.name for g in gs]
    G = dict(zip(names, gs))
    adj = {n: set() for n in names}
    for i, a in enumerate(gs):
        for b in gs[i + 1:]:
            if a.near(b, tol) and _touch(a, b, tol):
                adj[a.name].add(b.name)
                adj[b.name].add(a.name)
    todo = [n for n in names if G[n].mn.z <= ground + tol or n in anchors]
    seen = set(todo)
    while todo:
        for m in adj[todo.pop()]:
            if m not in seen:
                seen.add(m)
                todo.append(m)
    left, out = [n for n in names if n not in seen], []
    while left:
        grp, st = set(), [left[0]]
        while st:
            n = st.pop()
            if n not in grp:
                grp.add(n)
                st.extend(adj[n])
        left = [n for n in left if n not in grp]
        best, hit = min(G[n].mn.z for n in grp) - ground, "ground"
        for n in grp:
            for v in G[n].bm.verts:
                for t in gs:
                    if t.name in grp:
                        continue
                    r = t.bvh.ray_cast(v.co, _DOWN, best)
                    if r[0] is not None and r[3] <= best + 1e-6:
                        best, hit = r[3], t.name
        out.append(f"FLOATING {sorted(grp)}: gap {_n(best)} m above {hit}")
    for g in gs:
        g.free()
    return "\n".join(out)


def check_zfight(sel=None, tol=TOL, opposite=False):
    """Coplanar overlapping faces (same facing) between and inside objects.
    opposite=True also lists back-to-back coincident faces (normal contact, usually hidden)."""
    gs = _geos(sel)
    res = {}
    for a in gs:
        others = [b for b in gs if a.near(b, tol)]
        for f in a.bm.faces:
            if f.calc_area() < 1e-10:
                continue
            c, n = f.calc_center_median(), f.normal
            pts = [c] + [c.lerp(v.co, .5) for v in f.verts]
            nb = {lf.index for v in f.verts for lf in v.link_faces}
            for b in others:
                found = None
                for p in pts:
                    for loc, nrm, idx, d in b.bvh.find_nearest_range(p, tol):
                        if b is a and idx in nb:
                            continue
                        dot = n.dot(nrm)
                        if dot > .999 or (opposite and dot < -.999):
                            found = ("zfight" if dot > 0 else "back-to-back", p)
                            break
                    if found:
                        break
                if found:
                    key = (tuple(sorted((a.name, b.name))), found[0])
                    cnt = res.setdefault(key, {})
                    cnt[a.name] = cnt.get(a.name, 0) + 1
                    cnt.setdefault("at", found[1].copy())
    out = []
    for (pair, kind), cnt in sorted(res.items()):
        at = cnt.pop("at")
        who = pair[0] if pair[0] == pair[1] else f"{pair[0]} <> {pair[1]}"
        out.append(f"{kind.upper()} {who}: {max(cnt.values())} faces, e.g. at {_v(at)}")
    for g in gs:
        g.free()
    return "\n".join(out)


def check_all(sel=None, ground=0.0, anchors=(), ignore=()):
    """All checks; prints only problems."""
    parts = [("transforms", check_transforms(sel)), ("mesh", check_mesh(sel)),
             ("floating", check_floating(sel, ground, anchors=anchors, ignore=ignore)),
             ("zfight", check_zfight(sel))]
    bad = [f"[{k}]\n{v}" for k, v in parts if v]
    return f"checked {len(objs(sel))} meshes\n" + ("\n".join(bad) if bad else "ALL OK")


# ---------------------------------------------------------------- node trees
_BASE = {p.identifier for p in bpy.types.Node.bl_rna.properties}
_SHORT = (("GeometryNode", "GN."), ("ShaderNode", "SN."), ("FunctionNode", "FN."),
          ("NodeGroup", "Group"), ("CompositorNode", "CN."))


def _val(x):
    if hasattr(x, "name"):
        return x.name
    if hasattr(x, "__len__") and not isinstance(x, str):
        return _v(x)
    return _n(x) if isinstance(x, float) else repr(x)


_DEF = {}


def _defaults(nd, tree_type):
    """Default prop/input values of a node type (from a temp node, cached)."""
    key = nd.bl_idname
    if key not in _DEF:
        tmp = bpy.data.node_groups.new("_kt_tmp", tree_type)
        try:
            n = tmp.nodes.new(key)
            props = {p.identifier: _val(getattr(n, p.identifier)) for p in n.bl_rna.properties
                     if p.identifier not in _BASE and p.type in ("ENUM", "BOOLEAN", "INT", "FLOAT", "STRING")}
            ins = {s.identifier: _val(s.default_value) for s in n.inputs if hasattr(s, "default_value")}
            _DEF[key] = (props, ins)
        except Exception:
            _DEF[key] = ({}, {})
        finally:
            bpy.data.node_groups.remove(tmp)
    return _DEF[key]


def _tree(t, full=False, label=None):
    L = [f"## {label or t.name} ({t.bl_idname})"]
    for it in t.interface.items_tree:
        if getattr(it, "item_type", "") != "SOCKET":
            continue
        d = f" default={_val(it.default_value)}" if hasattr(it, "default_value") else ""
        L.append(f"  {it.in_out} {it.name}: {it.socket_type.replace('NodeSocket', '')}{d}")
    for nd in t.nodes:
        if nd.bl_idname in ("NodeFrame",):
            continue
        tid = nd.bl_idname
        for a, b in _SHORT:
            tid = tid.replace(a, b)
        dp, di = ({}, {}) if full else _defaults(nd, t.bl_idname)
        props = []
        for p in nd.bl_rna.properties:
            if p.identifier in _BASE or p.identifier.startswith("bl_"):
                continue
            if p.type in ("ENUM", "BOOLEAN", "INT", "FLOAT", "STRING") and not p.is_readonly:
                val = _val(getattr(nd, p.identifier))
                if dp.get(p.identifier) != val:
                    props.append(f"{p.identifier}={val}")
            elif p.type == "POINTER" and getattr(nd, p.identifier, None) is not None \
                    and hasattr(getattr(nd, p.identifier), "name"):
                props.append(f"{p.identifier}={getattr(nd, p.identifier).name}")
        ins = [f"{s.name}={_val(s.default_value)}" for s in nd.inputs
               if not s.is_linked and s.enabled and not s.hide and hasattr(s, "default_value")
               and di.get(s.identifier) != _val(s.default_value)]
        L.append(f"  {nd.name} [{tid}]" + (f" '{nd.label}'" if nd.label else "")
                 + (" {" + ", ".join(props) + "}" if props else "")
                 + (" in: " + ", ".join(ins) if ins else ""))
    for lk in t.links:
        L.append(f"  {lk.from_node.name}.{lk.from_socket.name} -> {lk.to_node.name}.{lk.to_socket.name}"
                 + ("" if lk.is_valid else " INVALID") + (" MUTED" if lk.is_muted else ""))
    return L


def nodes(target, full=False):
    """Text dump of a node tree: node group / material name, or object
    (its GN modifiers with their input values + its materials).
    Only non-default props/inputs are listed unless full=True."""
    L, trees = [], []
    if target in bpy.data.node_groups:
        trees = [(None, bpy.data.node_groups[target])]
    elif target in bpy.data.materials:
        trees = [(f"material {target}", bpy.data.materials[target].node_tree)]
    elif target in bpy.data.objects:
        o = bpy.data.objects[target]
        for m in o.modifiers:
            if m.type == "NODES" and m.node_group:
                vals = []
                for it in m.node_group.interface.items_tree:
                    if getattr(it, "in_out", "") == "INPUT" and it.socket_type != "NodeSocketGeometry":
                        try:
                            vals.append(f"{it.name}={_val(_in_get(m, it.identifier))}")
                        except Exception:
                            pass
                L.append(f"modifier {m.name} -> {m.node_group.name}: " + ", ".join(vals))
                trees.append((None, m.node_group))
        trees += [(f"material {s.material.name}", s.material.node_tree) for s in o.material_slots
                  if s.material and s.material.node_tree]
    else:
        return f"'{target}' is not a node group, material or object"
    for label, t in trees:
        L += _tree(t, full, label)
    return "\n".join(L)


def set_input(obj, input_name, value, modifier=None):
    """Set a Geometry Nodes modifier input by its visible name."""
    o = bpy.data.objects[obj] if isinstance(obj, str) else obj
    m = _gn_mod(o, modifier)
    _in_set(m, _mod_ident(m, input_name), value)
    o.update_tag()
    return f"{o.name}.{m.name}: {input_name}={_val(value)}"


# ---------------------------------------------------------------- actions (modify!)
def set_origin(sel, where="bottom"):
    """Move origin without moving the mesh. where: 'bottom' | 'center' | 'top' | 'cursor'
    | (fx, fy, fz) fractions of own bbox (0=min, .5=mid, 1=max) | world Vector."""
    out = []
    for o in objs(sel):
        me = o.data
        if me.users > 1:
            out.append(f"{o.name}: SKIPPED shared mesh {me.name}")
            continue
        co = [v.co for v in me.vertices]
        mn = Vector([min(c[i] for c in co) for i in range(3)])
        mx = Vector([max(c[i] for c in co) for i in range(3)])
        fr = {"bottom": (.5, .5, 0), "center": (.5, .5, .5), "top": (.5, .5, 1)}.get(where, where)
        if fr == "cursor":
            off = o.matrix_world.inverted() @ bpy.context.scene.cursor.location
        elif isinstance(fr, Vector):
            off = o.matrix_world.inverted() @ fr
        else:
            off = Vector([mn[i] + (mx[i] - mn[i]) * fr[i] for i in range(3)])
        T = Matrix.Translation(off)
        me.transform(Matrix.Translation(-off))
        o.matrix_world = o.matrix_world @ T
        for c in o.children:
            c.matrix_parent_inverse = Matrix.Translation(-off) @ c.matrix_parent_inverse
        out.append(f"{o.name}: origin[{_origin_label(o)}] world{_v(o.matrix_world.translation)}")
    return "\n".join(out)


def _with_selection(obs, fn):
    vl = bpy.context.view_layer
    prev = [o for o in vl.objects if o.select_get()]
    prev_act = vl.objects.active
    for o in vl.objects:
        o.select_set(o in obs)
    vl.objects.active = obs[0]
    try:
        with bpy.context.temp_override(selected_objects=obs, selected_editable_objects=obs,
                                       active_object=obs[0], object=obs[0]):
            return fn()
    finally:
        for o in vl.objects:
            o.select_set(o in prev)
        vl.objects.active = prev_act


def apply_transforms(sel, location=False, rotation=True, scale=True):
    obs = objs(sel, None)
    shared = [o.name for o in obs if o.data and o.data.users > 1]
    if shared:
        return f"SKIPPED: shared data on {shared} (make single user first)"
    _with_selection(obs, lambda: bpy.ops.object.transform_apply(
        location=location, rotation=rotation, scale=scale))
    return f"applied on {len(obs)} objects"


def clean_mesh(sel, merge=1e-4, loose=True, normals=True, interior=False, degenerate=True):
    """Fix garbage in base meshes. interior=True deletes faces whose every edge has >2 faces."""
    out = []
    for o in objs(sel):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        v0, f0 = len(bm.verts), len(bm.faces)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge)
        if degenerate:
            bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
        if interior:
            bad = [f for f in bm.faces if all(len(e.link_faces) > 2 for e in f.edges)]
            bmesh.ops.delete(bm, geom=bad, context="FACES_ONLY")
        if loose:
            bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context="EDGES")
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context="VERTS")
        if normals:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        out.append(f"{o.name}: verts {v0}->{len(bm.verts)}, faces {f0}->{len(bm.faces)}")
        bm.to_mesh(o.data)
        o.data.update()
        bm.free()
    return "\n".join(out)


def drop(sel, onto=None, gap=0.0, ground=0.0):
    """Move objects straight down until they touch the surface below (onto=objects to
    consider, default all visible meshes; falls back to the ground plane)."""
    out = []
    for o in objs(sel):
        dg = _dg()
        g = _Geo(o, dg)
        best, hit = g.mn.z - ground, "ground"
        for t in objs(onto):
            if t == o:
                continue
            tg = _Geo(t, dg)
            if tg.near(g, 0, axes=2) and tg.mn.z <= g.mx.z:
                for v in g.bm.verts:
                    r = tg.bvh.ray_cast(v.co + _UP * 1e-5, _DOWN)
                    if r[0] is not None and r[3] - 1e-5 <= best + 1e-6:
                        best, hit = r[3] - 1e-5, t.name
                for v in tg.bm.verts:
                    if g.mn.x <= v.co.x <= g.mx.x and g.mn.y <= v.co.y <= g.mx.y and v.co.z <= g.mn.z + 1e-5:
                        r = g.bvh.ray_cast(v.co - _UP * 1e-5, _UP)
                        if r[0] is not None and r[3] - 1e-5 <= best + 1e-6:
                            best, hit = r[3] - 1e-5, t.name
            tg.free()
        g.free()
        mw = o.matrix_world.copy()
        mw.translation.z -= best - gap
        o.matrix_world = mw
        out.append(f"{o.name}: moved {_n(-(best - gap))} m onto {hit}")
    return "\n".join(out)


def bake_shapekeys(obj, input_name, values, modifier=None, name=None):
    """Evaluate a GN modifier at several input values and store them as shape keys
    on a new object '<obj>_Baked' (first value = Basis). Topology must match."""
    o = bpy.data.objects[obj] if isinstance(obj, str) else obj
    m = _gn_mod(o, modifier)
    ident = _mod_ident(m, input_name)
    old = _in_get(m, ident)
    meshes = []
    try:
        for val in values:
            _in_set(m, ident, val)
            o.update_tag()
            dg = _dg()
            meshes.append(bpy.data.meshes.new_from_object(o.evaluated_get(dg)))
    finally:
        _in_set(m, ident, old)
        o.update_tag()
    counts = {len(me.vertices) for me in meshes}
    if len(counts) > 1:
        for me in meshes:
            bpy.data.meshes.remove(me)
        return f"FAILED: vertex count differs between values {sorted(counts)}"
    nb = bpy.data.objects.new(name or f"{o.name}_Baked", meshes[0])
    nb.matrix_world = o.matrix_world.copy()
    for c in o.users_collection:
        c.objects.link(nb)
    nb.shape_key_add(name="Basis")
    for val, me in zip(values[1:], meshes[1:]):
        sk = nb.shape_key_add(name=f"{input_name} {_val(val)}")
        co = [0.0] * (len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        sk.data.foreach_set("co", co)
        sk.value = 0.0
        bpy.data.meshes.remove(me)
    return f"{nb.name}: {len(values)} states, {len(meshes[0].vertices)} verts"


def export_fbx(sel, path, anim=False, **over):
    """FBX for Unity (selected objects only). anim=True: bake all actions + NLA strips as
    clips (all bones keyed, start/end forced). Override any exporter arg via kwargs."""
    obs = objs(sel, ("MESH", "ARMATURE", "EMPTY"))
    args = dict(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE", "EMPTY"},
                apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                axis_forward="-Z", axis_up="Y", use_space_transform=True,
                bake_space_transform=False, use_mesh_modifiers=True,
                mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=anim)
    if anim:
        args.update(bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True,
                    bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True,
                    bake_anim_step=1.0, bake_anim_simplify_factor=1.0)
    args.update(over)
    _with_selection(obs, lambda: bpy.ops.export_scene.fbx(**args))
    return f"exported {len(obs)} objects -> {path}"


def focus(sel=None, shading="MATERIAL"):
    """UI only: set viewport shading and frame objects (then take an area screenshot)."""
    obs = objs(sel, None)
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != "VIEW_3D":
                continue
            area.spaces.active.shading.type = shading
            region = next(r for r in area.regions if r.type == "WINDOW")
            if obs:
                def go():
                    with bpy.context.temp_override(window=win, area=area, region=region):
                        bpy.ops.view3d.view_selected()
                _with_selection(obs, go)
            return f"framed {len(obs)} objects, shading={shading}"
    return "no 3D viewport (background mode?)"


# ================================================================ textures / materials / UV / bake
_IMG_EXT = (".png", ".jpg", ".jpeg", ".tga", ".tif", ".tiff", ".exr", ".bmp", ".webp", ".hdr")
_MAP_KEYS = [  # checked in this order; tokens of the file name must match exactly
    ("arm", ("arm", "orm")),
    ("normal", ("normal", "normalgl", "normaldx", "nrm", "nor", "nrml")),
    ("gloss", ("glossiness", "gloss", "smoothness")),
    ("rough", ("roughness", "rough", "rgh")),
    ("metal", ("metallic", "metalness", "metal", "mtl")),
    ("ao", ("ambientocclusion", "occlusion", "ao")),
    ("height", ("height", "displacement", "disp", "bump")),
    ("alpha", ("opacity", "alpha")),
    ("emit", ("emission", "emissive", "emit")),
    ("base", ("basecolor", "albedo", "diffuse", "diff", "color", "colour", "col", "base")),
]
_DATA_MAPS = {"arm", "normal", "gloss", "rough", "metal", "ao", "height", "alpha"}


def _abs(path):
    if path.startswith("//") and not bpy.data.filepath:
        return os.path.join(bpy.app.tempdir, path[2:])
    return bpy.path.abspath(path)


def _classify(fname):
    toks = [t for t in re.split(r"[_\-\s.]+", os.path.splitext(fname)[0].lower()) if t]
    for kind, keys in _MAP_KEYS:
        if any(t in keys for t in toks):
            dx = kind == "normal" and any(t in ("dx", "directx", "normaldx") for t in toks)
            return kind, dx
    return None, False


def _img(src, colorspace=None):
    """Image by datablock name or file path (loaded once)."""
    if isinstance(src, bpy.types.Image):
        im = src
    elif src in bpy.data.images:
        im = bpy.data.images[src]
    else:
        im = bpy.data.images.load(_abs(src), check_existing=True)
    if colorspace:
        im.colorspace_settings.name = colorspace
    return im


def _mats(sel):
    out = []
    for o in objs(sel):
        for sl in o.material_slots:
            if sl.material and sl.material not in out:
                out.append(sl.material)
    return out


def _img_nodes(tree, seen=None):
    """(node, tree) for every Image Texture node, recursing into groups."""
    seen = seen if seen is not None else set()
    if tree is None or tree.name in seen and tree.bl_idname != "ShaderNodeTree":
        return []
    seen.add(tree.name)
    res = []
    for nd in tree.nodes:
        if nd.bl_idname == "ShaderNodeTexImage" and nd.image:
            res.append((nd, tree))
        elif nd.bl_idname == "ShaderNodeGroup" and nd.node_tree:
            res += _img_nodes(nd.node_tree, seen)
    return res


def _downstream(nd, depth=4):
    """Socket names an image node finally feeds (follows through simple nodes)."""
    out, todo = set(), [(nd, 0)]
    while todo:
        n, d = todo.pop()
        for so in n.outputs:
            for lk in so.links:
                tn = lk.to_node
                if tn.bl_idname in ("ShaderNodeBsdfPrincipled", "ShaderNodeOutputMaterial") or d >= depth:
                    out.add(lk.to_socket.name)
                else:
                    todo.append((tn, d + 1))
    return out


def assign_material(sel, mat, mode="replace"):
    """mode 'replace' -> object gets only this material; 'append' -> add a slot."""
    m = bpy.data.materials[mat] if isinstance(mat, str) else mat
    out = []
    for o in objs(sel):
        if mode == "replace":
            o.data.materials.clear()
        o.data.materials.append(m)
        out.append(o.name + (f" (shared mesh {o.data.name}!)" if o.data.users > 1 else ""))
    return f"{m.name} -> " + ", ".join(out)


def pbr_material(name, folder=None, files=None, sel=None, prefix=None, uv_scale=1.0,
                 normal_strength=1.0, height=False, ao_multiply=False, replace=False):
    """Build a Principled material from a texture set.
    folder: auto-detect maps by file name (basecolor/albedo, normal[_dx], roughness, gloss,
    metallic, ao, height, opacity, emission, arm/orm); prefix filters files in the folder.
    files: {"base": path, "normal": path, ...} overrides/extends detection.
    DirectX normals (dx in name) get green inverted. sel: objects to assign it to."""
    found, dxn = {}, False
    if folder:
        fd = _abs(folder)
        for f in sorted(os.listdir(fd)):
            if not f.lower().endswith(_IMG_EXT) or (prefix and not f.lower().startswith(prefix.lower())):
                continue
            kind, dx = _classify(f)
            if kind and kind not in found:
                found[kind] = os.path.join(fd, f)
                dxn = dxn or dx
    for k, v in (files or {}).items():
        found[k] = v
        if k == "normal":
            dxn = _classify(os.path.basename(v))[1]
    if not found:
        return f"no texture maps found in {folder}"
    if name in bpy.data.materials and not replace:
        return f"material '{name}' exists (replace=True to rebuild)"
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
    bs = N.new("ShaderNodeBsdfPrincipled"); bs.location = (500, 0)
    Lk.new(bs.outputs[0], out.inputs["Surface"])
    tc = N.new("ShaderNodeTexCoord"); tc.location = (-900, 0)
    mp = N.new("ShaderNodeMapping"); mp.location = (-700, 0)
    mp.inputs["Scale"].default_value = (uv_scale,) * 3 if isinstance(uv_scale, (int, float)) else uv_scale
    Lk.new(tc.outputs["UV"], mp.inputs["Vector"])
    y = [400]

    def tex(kind):
        t = N.new("ShaderNodeTexImage")
        t.image = _img(found[kind], "Non-Color" if kind in _DATA_MAPS else "sRGB")
        t.label = kind
        t.location = (-400, y[0]); y[0] -= 300
        Lk.new(mp.outputs[0], t.inputs["Vector"])
        return t

    col = None
    if "base" in found:
        col = tex("base").outputs["Color"]
    if "ao" in found and ao_multiply and col is not None:
        ao = tex("ao")
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
        mx.location = (100, 400); mx.inputs["Factor"].default_value = 1.0
        Lk.new(col, mx.inputs[6]); Lk.new(ao.outputs["Color"], mx.inputs[7])
        col = mx.outputs[2]
    if col is not None:
        Lk.new(col, bs.inputs["Base Color"])
    if "arm" in found:
        a = tex("arm")
        sc = N.new("ShaderNodeSeparateColor"); sc.location = (100, y[0] + 300)
        Lk.new(a.outputs["Color"], sc.inputs[0])
        if "rough" not in found:
            Lk.new(sc.outputs[1], bs.inputs["Roughness"])
        if "metal" not in found:
            Lk.new(sc.outputs[2], bs.inputs["Metallic"])
    if "rough" in found:
        Lk.new(tex("rough").outputs["Color"], bs.inputs["Roughness"])
    elif "gloss" in found:
        g = tex("gloss")
        inv = N.new("ShaderNodeInvert"); inv.location = (100, y[0] + 300)
        Lk.new(g.outputs["Color"], inv.inputs["Color"]); Lk.new(inv.outputs[0], bs.inputs["Roughness"])
    if "metal" in found:
        Lk.new(tex("metal").outputs["Color"], bs.inputs["Metallic"])
    if "alpha" in found:
        Lk.new(tex("alpha").outputs["Color"], bs.inputs["Alpha"])
    if "emit" in found:
        Lk.new(tex("emit").outputs["Color"], bs.inputs["Emission Color"])
        bs.inputs["Emission Strength"].default_value = 1.0
    nrm = None
    if "normal" in found:
        t = tex("normal")
        nm = N.new("ShaderNodeNormalMap"); nm.location = (200, y[0] + 300)
        nm.inputs["Strength"].default_value = normal_strength
        src = t.outputs["Color"]
        if dxn:
            sc = N.new("ShaderNodeSeparateColor"); sc.location = (-100, y[0] + 300)
            iv = N.new("ShaderNodeMath"); iv.operation = "SUBTRACT"; iv.inputs[0].default_value = 1.0
            iv.location = (0, y[0] + 300)
            cc = N.new("ShaderNodeCombineColor"); cc.location = (100, y[0] + 300)
            Lk.new(src, sc.inputs[0]); Lk.new(sc.outputs[0], cc.inputs[0])
            Lk.new(sc.outputs[1], iv.inputs[1]); Lk.new(iv.outputs[0], cc.inputs[1])
            Lk.new(sc.outputs[2], cc.inputs[2]); src = cc.outputs[0]
        Lk.new(src, nm.inputs["Color"])
        nrm = nm.outputs["Normal"]
    if "height" in found and height:
        bp = N.new("ShaderNodeBump"); bp.location = (300, y[0])
        Lk.new(tex("height").outputs["Color"], bp.inputs["Height"])
        if nrm is not None:
            Lk.new(nrm, bp.inputs["Normal"])
        nrm = bp.outputs["Normal"]
    if nrm is not None:
        Lk.new(nrm, bs.inputs["Normal"])
    used = ", ".join(f"{k}={os.path.basename(v)}" for k, v in found.items())
    res = f"{m.name}: {used}" + (" (normal DX->GL)" if dxn else "")
    if "height" in found and not height:
        res += " | height found, not used (height=True)"
    if "ao" in found and not ao_multiply:
        res += " | ao found, not used (ao_multiply=True)"
    if sel is not None:
        res += "\n" + assign_material(sel, m)
    return res


def check_textures(sel=None, max_size=2048):
    """Images used by the objects' materials: size, source, missing files,
    non-power-of-two, oversize, wrong color space for data maps. Also objects without UV."""
    rows, out = {}, []
    for m in _mats(sel):
        for nd, tr in _img_nodes(m.node_tree):
            im = nd.image
            r = rows.setdefault(im.name, {"im": im, "mats": set(), "feeds": set()})
            r["mats"].add(m.name)
            r["feeds"] |= _downstream(nd)
    for name, r in rows.items():
        im = r["im"]
        w, h = im.size
        src = "packed" if im.packed_file else ("generated" if im.source == "GENERATED" else "file")
        fl = []
        if src == "file" and not os.path.exists(_abs(im.filepath)):
            fl.append("MISSING FILE " + im.filepath)
        if w and (w & (w - 1) or h & (h - 1)):
            fl.append("NPOT")
        if max(w, h) > max_size:
            fl.append(f">{max_size}")
        data = r["feeds"] & {"Normal", "Roughness", "Metallic", "Alpha", "Height", "Color"} - {"Color"}
        if data and im.colorspace_settings.name not in ("Non-Color", "Raw", "Linear Rec.709"):
            fl.append(f"{im.colorspace_settings.name} on data ({','.join(sorted(data))})")
        if "Base Color" in r["feeds"] and im.colorspace_settings.name == "Non-Color":
            fl.append("Non-Color on Base Color")
        out.append(f"{name} {w}x{h} {src} {im.colorspace_settings.name} -> {','.join(sorted(r['feeds'])) or '?'}"
                   f" [{','.join(sorted(r['mats']))}]" + (" !" + "; ".join(fl) if fl else ""))
    for o in objs(sel):
        if any(sl.material for sl in o.material_slots) and not o.data.uv_layers:
            out.append(f"{o.name}: NO UV MAP")
        if not o.material_slots or not any(sl.material for sl in o.material_slots):
            out.append(f"{o.name}: no material")
    return "\n".join(out) or "no textures"


def resize_images(target=None, max_size=1024, pot=False, suffix=True):
    """Downscale images bigger than max_size (keeps aspect; pot=True -> power of two).
    target: image names list, or objects sel (their materials' images), None = all used.
    File images are saved as '<name>_<max>.<ext>' next to the original and relinked
    (original file untouched); suffix=False overwrites. Packed images are re-packed."""
    if target is None:
        ims = [r[0].image for m in bpy.data.materials if m.users for r in _img_nodes(m.node_tree)]
    elif isinstance(target, (list, tuple)) and all(isinstance(t, str) and t in bpy.data.images for t in target):
        ims = [bpy.data.images[t] for t in target]
    elif isinstance(target, str) and target in bpy.data.images:
        ims = [bpy.data.images[target]]
    else:
        ims = [r[0].image for m in _mats(target) for r in _img_nodes(m.node_tree)]
    out, done = [], set()
    for im in ims:
        if im.name in done:
            continue
        done.add(im.name)
        w, h = im.size
        if max(w, h) <= max_size:
            continue
        k = max_size / max(w, h)
        nw, nh = max(1, round(w * k)), max(1, round(h * k))
        if pot:
            nw, nh = 2 ** int(math.log2(nw)), 2 ** int(math.log2(nh))
        im.scale(nw, nh)
        msg = f"{im.name}: {w}x{h} -> {nw}x{nh}"
        if im.packed_file:
            im.pack()
            msg += " (repacked)"
        elif im.source == "FILE":
            src = _abs(im.filepath)
            base, ext = os.path.splitext(src)
            dst = f"{base}_{max_size}{ext}" if suffix else src
            im.filepath_raw = dst
            im.save()
            im.filepath = bpy.path.relpath(dst) if bpy.data.filepath else dst
            msg += f" saved {os.path.basename(dst)}"
        out.append(msg)
    return "\n".join(out) or f"nothing above {max_size}"


def relink_images(folder, recursive=True):
    """Find missing image files by file name inside folder and relink them."""
    idx = {}
    for root, _, fs in os.walk(_abs(folder)):
        for f in fs:
            idx.setdefault(f.lower(), os.path.join(root, f))
        if not recursive:
            break
    out = []
    for im in bpy.data.images:
        if im.source != "FILE" or im.packed_file or os.path.exists(_abs(im.filepath)):
            continue
        hit = idx.get(os.path.basename(bpy.path.abspath(im.filepath)).lower())
        if hit:
            im.filepath = hit
            im.reload()
            out.append(f"{im.name}: relinked {hit}")
        else:
            out.append(f"{im.name}: NOT FOUND ({os.path.basename(im.filepath)})")
    return "\n".join(out) or "no missing images"


def _pixels(im, size=None):
    if size and tuple(im.size) != tuple(size):
        im = im.copy()
        im.scale(*size)
        tmp = im
    else:
        tmp = None
    a = np.empty(len(im.pixels), dtype=np.float32)
    im.pixels.foreach_get(a)
    if tmp:
        bpy.data.images.remove(tmp)
    return a.reshape(-1, 4)


def pack_metal_smooth(out_path, metal=None, rough=None, metal_ch=0, rough_ch=0,
                      gloss=False, metal_value=0.0):
    """Unity URP Lit 'Metallic Map': RGB = metallic, A = smoothness (1 - roughness).
    metal/rough: image name or path (arm/orm: rough_ch=1, metal_ch=2). gloss=True if
    the rough map is already smoothness. Import in Unity with sRGB off."""
    srcs = [s for s in (metal, rough) if s]
    if not srcs:
        return "need metal and/or rough"
    ims = [_img(s, "Non-Color") for s in srcs]
    size = max((tuple(i.size) for i in ims), key=lambda s: s[0] * s[1])
    mt = _pixels(_img(metal, "Non-Color"), size)[:, metal_ch] if metal else np.full(size[0] * size[1], metal_value, np.float32)
    if rough:
        r = _pixels(_img(rough, "Non-Color"), size)[:, rough_ch]
        sm = r if gloss else 1.0 - r
    else:
        sm = np.full_like(mt, 0.5)
    px = np.stack([mt, mt, mt, sm], axis=1).ravel()
    im = bpy.data.images.new(os.path.splitext(os.path.basename(out_path))[0], size[0], size[1], alpha=True)
    im.colorspace_settings.name = "Non-Color"
    im.alpha_mode = "STRAIGHT"
    im.pixels.foreach_set(px)
    im.filepath_raw = _abs(out_path)
    im.file_format = "PNG"
    im.save()
    return f"saved {im.filepath_raw} {size[0]}x{size[1]} (R=metal, A=smoothness)"


# ---------------------------------------------------------------- UV
def _edit(o, fn):
    """Run fn() in Edit Mode on one object with everything selected."""
    vl = bpy.context.view_layer
    prev_act, prev = vl.objects.active, [x for x in vl.objects if x.select_get()]
    for x in vl.objects:
        x.select_set(x == o)
    vl.objects.active = o
    try:
        with bpy.context.temp_override(active_object=o, object=o, edit_object=o,
                                       selected_objects=[o], selected_editable_objects=[o]):
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            try:
                fn()
            finally:
                bpy.ops.object.mode_set(mode="OBJECT")
    finally:
        for x in vl.objects:
            x.select_set(x in prev)
        vl.objects.active = prev_act


def _uv_layer(o, layer):
    uvs = o.data.uv_layers
    if layer is None:
        return uvs.active or uvs.new(name="UVMap")
    lay = uvs.get(layer) or uvs.new(name=layer)
    uvs.active = lay
    return lay


def uv_unwrap(sel, method="smart", angle=66.0, margin=0.01, layer=None, size=1.0):
    """method: 'smart' (Smart UV Project) | 'unwrap' (by seams) | 'cube' (cube_size=size)
    | 'lightmap' (Lightmap Pack, no overlaps). layer: UV map name to create/use
    (e.g. 'Lightmap' as 2nd channel for Unity lightmaps)."""
    out = []
    for o in objs(sel):
        lay = _uv_layer(o, layer)
        if method == "smart":
            f = lambda: bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin)
        elif method == "unwrap":
            f = lambda: bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=margin)
        elif method == "cube":
            f = lambda: bpy.ops.uv.cube_project(cube_size=size)
        elif method == "lightmap":
            f = lambda: bpy.ops.uv.lightmap_pack(PREF_CONTEXT="ALL_FACES", PREF_MARGIN_DIV=max(0.05, margin * 20))
        else:
            return f"unknown method {method}"
        ln = lay.name
        _edit(o, f)
        names = [u.name for u in o.data.uv_layers]
        out.append(f"{o.name}: {method} -> {ln} (channel {names.index(ln)})")
    return "\n".join(out)


def uv_box(sel, size=1.0, layer=None, world=True):
    """Box projection written directly (no operator): each face projected on its dominant
    axis, 1 texture tile = `size` meters. world=True -> seamless tiling across objects
    (walls, floors of a modular kit). Orientation: textures upright on walls, not mirrored."""
    out = []
    for o in objs(sel):
        lay = _uv_layer(o, layer)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        uvl = bm.loops.layers.uv.get(lay.name) or bm.loops.layers.uv.new(lay.name)
        mw = o.matrix_world if world else Matrix.Diagonal(o.matrix_world.to_scale()).to_4x4()
        nmat = mw.to_3x3().inverted_safe().transposed()
        for f in bm.faces:
            n = (nmat @ f.normal).normalized()
            ax = max(range(3), key=lambda i: abs(n[i]))
            sg = 1 if n[ax] >= 0 else -1
            for lp in f.loops:
                c = mw @ lp.vert.co
                if ax == 0:
                    u, v = sg * c.y, c.z
                elif ax == 1:
                    u, v = -sg * c.x, c.z
                else:
                    u, v = c.x, sg * c.y
                lp[uvl].uv = (u / size, v / size)
        bm.to_mesh(o.data)
        bm.free()
        out.append(o.name)
    return f"box UV ({size} m/tile, {'world' if world else 'local'}) on: " + ", ".join(out)


def check_uv(sel=None, tex_size=1024, grid=256):
    """Per object: UV maps, texel density (px/m at tex_size), share outside 0-1,
    overlapping area % (needs 0% for baking/lightmaps; fine for tiling textures)."""
    out = []
    for o in objs(sel):
        me = o.data
        if not me.uv_layers:
            out.append(f"{o.name}: NO UV")
            continue
        uvl = me.uv_layers.active
        me.calc_loop_triangles()
        nt = len(me.loop_triangles)
        if not nt:
            continue
        li = np.empty(nt * 3, np.int32); me.loop_triangles.foreach_get("loops", li)
        vi = np.empty(nt * 3, np.int32); me.loop_triangles.foreach_get("vertices", vi)
        uv = np.empty(len(me.loops) * 2, np.float32); uvl.uv.foreach_get("vector", uv)
        uv = uv.reshape(-1, 2)[li].reshape(nt, 3, 2)
        co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co)
        M = np.array(o.matrix_world, dtype=np.float64)
        co = co.reshape(-1, 3) @ M[:3, :3].T
        p = co[vi].reshape(nt, 3, 3)
        a3 = 0.5 * np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1)
        e1, e2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
        auv = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])
        td = math.sqrt(auv.sum() / a3.sum()) * tex_size if a3.sum() > 0 else 0
        outside = float(np.mean((uv < -1e-4) | (uv > 1 + 1e-4)))
        # overlap raster (only inside 0-1)
        g = np.zeros((grid, grid), np.uint16)
        P = uv * grid
        for t in range(nt):
            tri = P[t]
            x0, y0 = np.floor(tri.min(0)).astype(int)
            x1, y1 = np.ceil(tri.max(0)).astype(int)
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, grid), min(y1, grid)
            if x1 <= x0 or y1 <= y0:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1) + .5, np.arange(y0, y1) + .5)
            (ax, ay), (bx, by), (cx, cy) = tri
            d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(d) < 1e-12:
                continue
            l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / d
            l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / d
            m = (l1 >= 0) & (l2 >= 0) & (l1 + l2 <= 1)
            g[ys[m].astype(int), xs[m].astype(int)] += 1
        cov = int((g > 0).sum())
        ov = 100.0 * (g > 1).sum() / cov if cov else 0
        maps = ",".join(u.name + ("*" if u == uvl else "") for u in me.uv_layers)
        out.append(f"{o.name}: uv[{maps}] density {td:.0f} px/m @{tex_size}"
                   f" | outside 0-1 {outside * 100:.0f}% | overlap {ov:.1f}% | fill {100 * cov / grid / grid:.0f}%")
    return "\n".join(out)


# ---------------------------------------------------------------- bake
def bake(sel, maps=("DIFFUSE",), size=1024, out_dir="//baked", margin=8, uv=None,
         samples=16, source=None, extrusion=0.02, max_ray=0.0, make_material=False):
    """Cycles bake per object into PNGs '<obj>_<MAP>.png' in out_dir.
    maps: DIFFUSE (color only), NORMAL, ROUGHNESS, AO, EMIT, COMBINED, GLOSSY...
    source: high-poly objects -> 'selected to active' (normal bake hi->low).
    uv: UV map to bake into (needs no overlaps: check_uv / uv_unwrap 'lightmap').
    make_material=True -> builds '<obj>_Baked' material from the result and assigns it
    (do this on a copy if the original must stay)."""
    sc = bpy.context.scene
    old = (sc.render.engine, sc.cycles.samples)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    od = _abs(out_dir)
    os.makedirs(od, exist_ok=True)
    srcs = objs(source) if source else []
    out = []
    try:
        for o in objs(sel):
            if not o.data.uv_layers:
                out.append(f"{o.name}: NO UV, skipped")
                continue
            if uv:
                o.data.uv_layers.active = o.data.uv_layers[uv]
            if not any(sl.material for sl in o.material_slots):
                o.data.materials.append(bpy.data.materials.new(f"{o.name}_tmp"))
            files = {}
            for mp in maps:
                iname = f"{o.name}_{mp}"
                if iname in bpy.data.images:
                    bpy.data.images.remove(bpy.data.images[iname])
                im = bpy.data.images.new(iname, size, size, alpha=False)
                if mp not in ("DIFFUSE", "EMIT", "COMBINED", "GLOSSY"):
                    im.colorspace_settings.name = "Non-Color"
                tmp = []
                for sl in o.material_slots:
                    if not sl.material:
                        continue
                    nt = sl.material.node_tree
                    nd = nt.nodes.new("ShaderNodeTexImage")
                    nd.image = im
                    nt.nodes.active = nd
                    tmp.append((nt, nd))
                kw = dict(type=mp, margin=margin, use_clear=True)
                if mp == "DIFFUSE":
                    kw["pass_filter"] = {"COLOR"}
                if srcs:
                    kw.update(use_selected_to_active=True, cage_extrusion=extrusion, max_ray_distance=max_ray)
                obs = [o] + [s for s in srcs if s != o]
                try:
                    _with_selection(obs, lambda: bpy.ops.object.bake(**kw))
                finally:
                    for nt, nd in tmp:
                        nt.nodes.remove(nd)
                path = os.path.join(od, iname + ".png")
                im.filepath_raw = path
                im.file_format = "PNG"
                im.save()
                files[mp] = path
            out.append(f"{o.name}: " + ", ".join(os.path.basename(p) for p in files.values()))
            if make_material:
                kmap = {"DIFFUSE": "base", "NORMAL": "normal", "ROUGHNESS": "rough", "EMIT": "emit", "AO": "ao"}
                fs = {kmap[k]: v for k, v in files.items() if k in kmap}
                out.append(pbr_material(f"{o.name}_Baked", files=fs, sel=o, replace=True))
    finally:
        sc.render.engine, sc.cycles.samples = old
    return f"-> {od}\n" + "\n".join(out)


# ================================================================ animation (Blender 4.4+/5.x slotted actions)
from bpy_extras import anim_utils as _au

_CH = {"location": "loc", "rotation_quaternion": "rotq", "rotation_euler": "rot",
       "rotation_axis_angle": "rotaa", "scale": "scale"}
_LR = [(".L", ".R"), ("_L", "_R"), (".l", ".r"), ("_l", "_r"), ("Left", "Right"), ("left", "right")]


def _ob(o):
    return bpy.data.objects[o] if isinstance(o, str) else o


def _fcs(o):
    ad = o.animation_data
    if not ad or not ad.action:
        return []
    cb = _au.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    return list(cb.fcurves) if cb else []


def _split(dp):
    """'pose.bones["Arm.L"].rotation_quaternion' -> ('Arm.L', 'rotation_quaternion'); object -> ('', prop)."""
    m = re.match(r'pose\.bones\["(.+?)"\]\.(\w+)$', dp)
    return (m.group(1), m.group(2)) if m else ("", dp)


def _sel_fc(o, bones=None, frames=None):
    bs = None if bones is None else ({bones} if isinstance(bones, str) else set(bones))
    out = []
    for fc in _fcs(o):
        b, prop = _split(fc.data_path)
        if bs is None or b in bs:
            out.append(fc)
    return out


def _in(f, frames):
    return frames is None or frames[0] - 1e-4 <= f <= frames[1] + 1e-4


def _flip_name(n):
    for a, b in _LR:
        if n.endswith(a):
            return n[:-len(a)] + b
        if n.endswith(b):
            return n[:-len(b)] + a
    return n


def _target(o, bone):
    return o.pose.bones[bone] if bone else o


def set_range(start, end, fps=None):
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = int(start), int(end)
    if fps:
        sc.render.fps, sc.render.fps_base = int(fps), 1.0
    return f"range {sc.frame_start}-{sc.frame_end} @ {sc.render.fps / sc.render.fps_base:g} fps"


def anim_report(obj):
    """Action, slot, ranges and, per bone, animated channels with key frames."""
    o = _ob(obj)
    sc = bpy.context.scene
    ad = o.animation_data
    head = f"scene {sc.frame_start}-{sc.frame_end} @ {sc.render.fps / sc.render.fps_base:g} fps, current {sc.frame_current}"
    if not ad or not ad.action:
        return head + f"\n{o.name}: no action" + (f" | NLA: {[t.name for t in ad.nla_tracks]}" if ad and ad.nla_tracks else "")
    a = ad.action
    L = [head, f"{o.name}: action '{a.name}' slot '{ad.action_slot.name_display if ad.action_slot else '-'}'"
               f" keys {_n(a.curve_frame_range[0])}-{_n(a.curve_frame_range[1])}"
               + (" CYCLIC" if a.use_cyclic else "")
               + (f" | NLA: {[t.name for t in ad.nla_tracks]}" if ad.nla_tracks else "")
               + f" | other actions: {[x.name for x in bpy.data.actions if x != a][:10]}"]
    per = {}
    for fc in _fcs(o):
        b, prop = _split(fc.data_path)
        d = per.setdefault(b or "(object)", {"ch": set(), "fr": set(), "ip": set(), "mod": set()})
        d["ch"].add(_CH.get(prop, prop))
        d["fr"] |= {round(k.co.x, 2) for k in fc.keyframe_points}
        d["ip"] |= {k.interpolation for k in fc.keyframe_points}
        d["mod"] |= {m.type for m in fc.modifiers}
    for b, d in per.items():
        fr = sorted(d["fr"])
        frs = " ".join(_n(f) for f in fr) if len(fr) <= 16 else f"{_n(fr[0])}..{_n(fr[-1])} ({len(fr)} keys)"
        L.append(f"  {b}: {','.join(sorted(d['ch']))} @ {frs} [{','.join(sorted(d['ip']))}]"
                 + (f" mods={','.join(sorted(d['mod']))}" if d["mod"] else ""))
    return "\n".join(L)


def keys(obj, bones=None, frames=None, maxk=30):
    """Key values per channel: 'Arm.L rot[0]: 1=0 10=45 (BEZIER)'. Rotations in degrees
    for euler; quaternions raw."""
    o = _ob(obj)
    L = []
    for fc in _sel_fc(o, bones):
        b, prop = _split(fc.data_path)
        conv = 57.2958 if prop == "rotation_euler" else 1.0
        ks = [k for k in fc.keyframe_points if _in(k.co.x, frames)][:maxk]
        if not ks:
            continue
        L.append(f"{b or o.name} {_CH.get(prop, prop)}[{fc.array_index}]: "
                 + " ".join(f"{_n(k.co.x)}={_n(k.co.y * conv)}" for k in ks)
                 + f" ({','.join(sorted({k.interpolation for k in ks}))})")
    return "\n".join(L) or "no keys"


def pose_at(obj, frame, bones=None):
    """Local loc / rot (euler deg) / scale and world head position per bone at a frame."""
    o = _ob(obj)
    sc = bpy.context.scene
    old = sc.frame_current
    sc.frame_set(int(frame))
    L = []
    items = [("", o)] if o.type != "ARMATURE" else [(pb.name, pb) for pb in o.pose.bones
                                                     if bones is None or pb.name in ([bones] if isinstance(bones, str) else bones)]
    for name, t in items:
        rq = t.rotation_quaternion if t.rotation_mode == "QUATERNION" else t.rotation_euler.to_quaternion()
        e = rq.to_euler("XYZ")
        wp = (o.matrix_world @ t.head) if name else o.matrix_world.translation
        L.append(f"{name or o.name}: loc{_v(t.location)} rot{_v([x * 57.2958 for x in e])}deg"
                 f" scale{_v(t.scale)} world{_v(wp)}")
    sc.frame_set(old)
    return f"frame {frame}\n" + "\n".join(L)


def key_pose(obj, frame, pose, interp=None, relative=False):
    """Set and key transforms. pose = {"BoneName": {"loc": (x,y,z), "rot": (x,y,z) deg,
    "scale": (x,y,z)}, "": {...} for the object itself}. Rotation is converted to the
    bone's rotation mode and kept continuous with the previous key. relative=True adds
    to the pose evaluated at that frame. interp: 'BEZIER' | 'LINEAR' | 'CONSTANT' for the new keys."""
    o = _ob(obj)
    sc = bpy.context.scene
    sc.frame_set(int(frame))
    done = []
    for bone, tr in pose.items():
        t = _target(o, bone)
        pre = f'pose.bones["{bone}"].' if bone else ""
        paths = []
        if "loc" in tr:
            t.location = (t.location + Vector(tr["loc"])) if relative else Vector(tr["loc"])
            paths.append("location")
        if "scale" in tr:
            sv = Vector(tr["scale"])
            t.scale = Vector([a * b for a, b in zip(t.scale, sv)]) if relative else sv
            paths.append("scale")
        if "rot" in tr:
            e = Euler([math.radians(x) for x in tr["rot"]], "XYZ")
            if t.rotation_mode == "QUATERNION":
                q = e.to_quaternion()
                if relative:
                    q = t.rotation_quaternion @ q
                q.make_compatible(t.rotation_quaternion)
                t.rotation_quaternion = q
                paths.append("rotation_quaternion")
            elif t.rotation_mode == "AXIS_ANGLE":
                q = e.to_quaternion()
                if relative:
                    aa = t.rotation_axis_angle
                    q = Quaternion(Vector(aa[1:]), aa[0]) @ q
                ax, ang = q.to_axis_angle()
                t.rotation_axis_angle = (ang, *ax)
                paths.append("rotation_axis_angle")
            else:
                cur = t.rotation_euler.copy()
                if relative:
                    q = cur.to_quaternion() @ e.to_quaternion()
                else:
                    q = e.to_quaternion()
                ne = q.to_euler(t.rotation_mode, cur)
                t.rotation_euler = ne
                paths.append("rotation_euler")
        for p in paths:
            t.keyframe_insert(p, frame=frame)
            if interp:
                for fc in _fcs(o):
                    if fc.data_path == pre + p:
                        for k in fc.keyframe_points:
                            if abs(k.co.x - frame) < 1e-4:
                                k.interpolation = interp
        done.append(f"{bone or o.name}:{','.join(_CH[p] for p in paths)}")
    return f"keyed f{frame}: " + " ".join(done)


def squash_stretch(obj, bone, frame, factor, axis="Y"):
    """Volume-preserving scale key: `axis` *= factor, other two /= sqrt(factor).
    factor <1 squash, >1 stretch. Bone length axis is Y."""
    k = 1 / math.sqrt(factor)
    sc = {"X": (factor, k, k), "Y": (k, factor, k), "Z": (k, k, factor)}[axis]
    return key_pose(obj, frame, {bone: {"scale": sc}})


def move_keys(obj, offset=0.0, scale=1.0, pivot=None, bones=None, frames=None, snap=True):
    """Shift and/or retime keys (with handles). scale 2 = twice slower around pivot
    (default: first selected key). snap=True rounds keys to whole frames."""
    o = _ob(obj)
    fcs = _sel_fc(o, bones)
    ks = [k for fc in fcs for k in fc.keyframe_points if _in(k.co.x, frames)]
    if not ks:
        return "no keys"
    pv = min(k.co.x for k in ks) if pivot is None else pivot
    f = lambda x: pv + (x - pv) * scale + offset
    for k in ks:
        nx = f(k.co.x)
        nx = round(nx) if snap else nx
        d = nx - k.co.x
        k.handle_left.x = k.co.x + d + (k.handle_left.x - k.co.x) * scale
        k.handle_right.x = k.co.x + d + (k.handle_right.x - k.co.x) * scale
        k.co.x = nx
    for fc in fcs:
        fc.update()
    return f"{len(ks)} keys moved (offset {offset}, scale {scale}, pivot {_n(pv)})"


def set_interp(obj, interp="BEZIER", easing="AUTO", handles=None, bones=None, frames=None):
    """interp: BEZIER/LINEAR/CONSTANT/SINE/QUAD/CUBIC/BACK/BOUNCE/ELASTIC...;
    handles: AUTO_CLAMPED/AUTO/VECTOR/ALIGNED/FREE."""
    n = 0
    for fc in _sel_fc(_ob(obj), bones):
        for k in fc.keyframe_points:
            if _in(k.co.x, frames):
                k.interpolation = interp
                k.easing = easing
                if handles:
                    k.handle_left_type = k.handle_right_type = handles
                n += 1
        fc.update()
    return f"{n} keys -> {interp} {easing}" + (f" {handles}" if handles else "")


def cycle(obj, bones=None, end=None):
    """Make a loop: Cycles modifier on curves; if end given, key at `end` = value at first key
    (so frame end == frame start -> seamless)."""
    n = 0
    for fc in _sel_fc(_ob(obj), bones):
        if not fc.keyframe_points:
            continue
        if not any(m.type == "CYCLES" for m in fc.modifiers):
            fc.modifiers.new("CYCLES")
        if end is not None:
            first = fc.keyframe_points[0]
            fc.keyframe_points.insert(end, first.co.y, options={"REPLACE"})
        fc.update()
        n += 1
    return f"cycles on {n} curves" + (f", end key {end}" if end is not None else "")


def dup_action(obj, name=None):
    """Work on a copy: duplicate the current action and assign it (original stays)."""
    o = _ob(obj)
    ad = o.animation_data
    if not ad or not ad.action:
        return "no action"
    src = ad.action
    slot = ad.action_slot
    a = src.copy()
    a.name = name or src.name + "_edit"
    src.use_fake_user = True
    ad.action = a
    if slot:
        s2 = a.slots.get(slot.identifier)
        if s2:
            ad.action_slot = s2
    return f"{o.name}: now '{a.name}' (original '{src.name}' kept with fake user)"


def copy_keys(src, dst=None, bones=None, bone_map=None, frames=None, offset=0.0,
              mirror=False, replace=True):
    """Copy keys between bones/objects. bone_map {"src": "dst"}; mirror=True maps .L<->.R
    and flips X (loc x, quat y/z, euler y/z) = Blender 'paste flipped' for X-symmetric rigs.
    frames=(a, b) source range, offset shifts in time. Same object allowed."""
    so = _ob(src)
    do = _ob(dst) if dst else so
    if not do.animation_data:
        do.animation_data_create()
    if not do.animation_data.action:
        do.animation_data.action = bpy.data.actions.new(do.name + "Action")
    act = do.animation_data.action
    snap, warn = [], set()
    for fc in _sel_fc(so, bones):
        b, prop = _split(fc.data_path)
        db = bone_map.get(b, b) if bone_map else b
        sign = 1.0
        if mirror:
            db = _flip_name(db)
            i = fc.array_index
            if (prop == "location" and i == 0) or (prop == "rotation_quaternion" and i in (2, 3)) \
                    or (prop == "rotation_euler" and i in (1, 2)) or (prop == "rotation_axis_angle" and i in (2, 3)):
                sign = -1.0
        if db and do.type == "ARMATURE" and db not in do.pose.bones:
            continue
        if prop.startswith("rotation_"):
            dmode = (do.pose.bones[db] if db else do).rotation_mode
            have = {"QUATERNION": "rotation_quaternion", "AXIS_ANGLE": "rotation_axis_angle"}.get(dmode, "rotation_euler")
            if prop != have:
                warn.add(f"{db or do.name}: rotation mode {dmode} but source keys are {prop} (set the same mode)")
        ks = [(k.co.x, k.co.y, k.handle_left.x, k.handle_left.y, k.handle_right.x, k.handle_right.y,
               k.interpolation, k.easing, k.handle_left_type, k.handle_right_type)
              for k in fc.keyframe_points if _in(k.co.x, frames)]
        if ks:
            snap.append(((f'pose.bones["{db}"].{prop}' if db else prop), fc.array_index, db, sign, ks))
    n = 0
    for dp, idx, db, sign, ks in snap:
        fc = act.fcurve_ensure_for_datablock(do, dp, index=idx, group_name=db or "Object Transforms")
        if replace:
            lo, hi = ks[0][0] + offset, ks[-1][0] + offset
            for k in [k for k in fc.keyframe_points if lo - 1e-4 <= k.co.x <= hi + 1e-4][::-1]:
                fc.keyframe_points.remove(k)
        for x, y, hlx, hly, hrx, hry, ip, ea, hlt, hrt in ks:
            k = fc.keyframe_points.insert(x + offset, y * sign, options={"FAST"})
            k.interpolation, k.easing = ip, ea
            k.handle_left_type, k.handle_right_type = hlt, hrt
            k.handle_left = (hlx + offset, hly * sign)
            k.handle_right = (hrx + offset, hry * sign)
            n += 1
        fc.update()
    return (f"copied {n} keys on {len(snap)} curves -> {do.name}" + (" (mirrored)" if mirror else "")
            + "".join("\nWARNING " + w for w in sorted(warn)))


def bake_anim(obj, start=None, end=None, step=1, visual=True, clear_constraints=False, name=None):
    """Bake the evaluated motion (constraints, IK, drivers) to plain keys on every bone
    into a NEW action (original action kept). Use before Unity export if the rig uses IK."""
    o = _ob(obj)
    sc = bpy.context.scene
    s, e = int(start if start is not None else sc.frame_start), int(end if end is not None else sc.frame_end)
    ad = o.animation_data
    src = ad.action if ad else None
    if src:
        src.use_fake_user = True
    obs = [o]
    def go():
        mode = o.mode
        if o.type == "ARMATURE":
            bpy.ops.object.mode_set(mode="POSE")
            bpy.ops.pose.select_all(action="SELECT")
        bpy.ops.nla.bake(frame_start=s, frame_end=e, step=step, only_selected=False,
                         visual_keying=visual, clear_constraints=clear_constraints,
                         use_current_action=False,
                         bake_types={"POSE"} if o.type == "ARMATURE" else {"OBJECT"})
        bpy.ops.object.mode_set(mode=mode if mode in ("OBJECT", "POSE") else "OBJECT")
    _with_selection(obs, go)
    a = o.animation_data.action
    if name and a:
        a.name = name
    return f"{o.name}: baked {s}-{e} step {step} -> '{a.name if a else '?'}'" + (f" (source '{src.name}' kept)" if src else "")


def motion(obj, bone=None, start=None, end=None, step=1, point="head"):
    """Trajectory text to judge arcs and spacing: world position per frame, speed
    (m/frame), and 'turn' angle of the path. point: head/tail (bones)."""
    o = _ob(obj)
    sc = bpy.context.scene
    s = int(start if start is not None else sc.frame_start)
    e = int(end if end is not None else sc.frame_end)
    old = sc.frame_current
    pts = []
    for f in range(s, e + 1, step):
        sc.frame_set(f)
        if bone:
            pb = o.pose.bones[bone]
            p = o.matrix_world @ (pb.head if point == "head" else pb.tail)
        else:
            p = o.matrix_world.translation.copy()
        pts.append((f, p.copy()))
    sc.frame_set(old)
    L = []
    for i, (f, p) in enumerate(pts):
        sp = (p - pts[i - 1][1]).length / step if i else 0
        turn = ""
        if 0 < i < len(pts) - 1:
            a, b = p - pts[i - 1][1], pts[i + 1][1] - p
            if a.length > 1e-6 and b.length > 1e-6:
                turn = f" turn {math.degrees(a.angle(b)):.0f}"
        L.append(f"f{f} {_v(p)} v={_n(sp)}{turn}")
    zs = [p.z for _, p in pts]
    return (f"{bone or o.name} {s}-{e}: z {_n(min(zs))}..{_n(max(zs))}, apex f{pts[zs.index(max(zs))][0]}\n"
            + "\n".join(L))


def anim_check(obj, ground=None, feet=(), tol=0.002):
    """Animation problems: quaternion sign flips, euler jumps >180, keys on sub-frames,
    zero/negative scale, and (with ground + feet bones) frames where feet go below ground."""
    o = _ob(obj)
    L = []
    groups = {}
    for fc in _fcs(o):
        b, prop = _split(fc.data_path)
        for k in fc.keyframe_points:
            if abs(k.co.x - round(k.co.x)) > 1e-3:
                L.append(f"{b or o.name} {_CH.get(prop, prop)}: key on sub-frame {_n(k.co.x)}")
                break
        if prop == "rotation_euler":
            kp = fc.keyframe_points
            for i in range(1, len(kp)):
                if abs(kp[i].co.y - kp[i - 1].co.y) > math.pi:
                    L.append(f"{b} rot[{fc.array_index}]: jump {math.degrees(kp[i].co.y - kp[i - 1].co.y):.0f}deg "
                             f"f{_n(kp[i - 1].co.x)}->f{_n(kp[i].co.x)}")
        if prop in ("rotation_quaternion", "scale"):
            groups.setdefault((b, prop), {})[fc.array_index] = fc
    for (b, prop), fcd in groups.items():
        frames = sorted({k.co.x for fc in fcd.values() for k in fc.keyframe_points})
        vals = [[fcd[i].evaluate(f) if i in fcd else (1.0 if prop == "scale" or i == 0 else 0.0)
                 for i in range(4 if prop == "rotation_quaternion" else 3)] for f in frames]
        for i in range(1, len(vals)):
            if prop == "rotation_quaternion" and sum(a * c for a, c in zip(vals[i], vals[i - 1])) < 0:
                L.append(f"{b} quaternion sign flip f{_n(frames[i - 1])}->f{_n(frames[i])} (spins the long way)")
        for f, v in zip(frames, vals):
            if prop == "scale" and min(v) <= 1e-4:
                L.append(f"{b} scale <=0 at f{_n(f)}")
                break
    if ground is not None and feet:
        sc = bpy.context.scene
        old = sc.frame_current
        low = {}
        for f in range(sc.frame_start, sc.frame_end + 1):
            sc.frame_set(f)
            for fb in feet:
                pb = o.pose.bones[fb]
                z = min((o.matrix_world @ pb.head).z, (o.matrix_world @ pb.tail).z)
                if z < ground - tol and (fb not in low or z < low[fb][1]):
                    low[fb] = (f, z)
        sc.frame_set(old)
        for fb, (f, z) in low.items():
            L.append(f"{fb} below ground, worst f{f} by {_n(ground - z)} m")
    return "\n".join(L) or "ALL OK"


def contact_sheet(path, frames, cols=4, width=480):
    """UI only: viewport render of several frames tiled into one PNG, then shown in an
    Image Editor if one is open (screenshot that area: one image instead of many)."""
    if bpy.app.background:
        return "contact_sheet needs Blender UI (background mode)"
    sc = bpy.context.scene
    win = area = region = None
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == "VIEW_3D":
                win, area, region = w, a, next(r for r in a.regions if r.type == "WINDOW")
                break
        if area:
            break
    if not area:
        return "no 3D viewport (background mode?)"
    old = (sc.frame_current, sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage)
    aspect = region.height / region.width
    sc.render.resolution_x, sc.render.resolution_y = width, int(width * aspect)
    sc.render.resolution_percentage = 100
    tiles = []
    tmp = os.path.join(bpy.app.tempdir, "_kt_frame.png")
    try:
        for f in frames:
            sc.frame_set(int(f))
            with bpy.context.temp_override(window=win, area=area, region=region):
                bpy.ops.render.opengl(view_context=True)
            bpy.data.images["Render Result"].save_render(tmp)
            im = bpy.data.images.load(tmp)
            a = np.empty(len(im.pixels), np.float32)
            im.pixels.foreach_get(a)
            tiles.append(a.reshape(im.size[1], im.size[0], 4))
            bpy.data.images.remove(im)
    finally:
        sc.frame_set(old[0])
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = old[1:]
    h, w = tiles[0].shape[:2]
    rows = math.ceil(len(tiles) / cols)
    sheet = np.ones((rows * h, cols * w, 4), np.float32)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        y0 = (rows - 1 - r) * h  # first frame top-left
        sheet[y0:y0 + h, c * w:c * w + w] = t
    name = os.path.basename(path)
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    im = bpy.data.images.new(name, cols * w, rows * h, alpha=True)
    im.pixels.foreach_set(sheet.ravel())
    im.filepath_raw = _abs(path)
    im.file_format = "PNG"
    im.save()
    shown = False
    for a in win.screen.areas:
        if a.type == "IMAGE_EDITOR":
            a.spaces.active.image = im
            shown = True
    return f"sheet {len(tiles)} frames {list(frames)} -> {im.filepath_raw}" + (" (shown in Image Editor)" if shown else "")
