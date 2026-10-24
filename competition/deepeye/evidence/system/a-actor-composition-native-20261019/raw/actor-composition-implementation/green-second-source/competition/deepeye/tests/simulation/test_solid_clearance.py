"""Mathematical solid certificates, not asset import or movement acceptance."""
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext
from fractions import Fraction as F
import importlib
import random
import unittest

try:
    s = importlib.import_module('competition.deepeye.simulation.authority.motion.solid_clearance')
except ModuleNotFoundError as exc:
    if exc.name != 'competition.deepeye.simulation.authority.motion.solid_clearance':
        raise
    s = None


class SolidClearanceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(s, 'solid_clearance implementation missing')
        self.errors = s.ErrorBounds(0, 0, 0, 0, 0, 'explicit exact fixture assumptions; not measurements')
        self.model = s.CapsuleModel('fixture-capsule', 'v1', F(2,5), F(3,25), F(13,25))

    def sweep(self, **changes):
        args = dict(model=self.model, start=(0,0,0), end=(0,0,2), quaternion=(0,0,0,1),
                    arc_length=2, curvature=0, rotation=0, errors=self.errors)
        args.update(changes)
        return s.Sweep(**args)

    def shape(self, kind='box', centre=(3,0,1), dimensions=(F(1,4),)*3, **changes):
        args = dict(model_id='fixture-part', version='v1', kind=kind, centre=centre,
                    dimensions=dimensions, quaternion=(0,0,0,1), vertices=())
        args.update(changes)
        return s.Solid(**args)

    def scene(self, shape=None, material='water'):
        shape = shape or self.shape()
        return s.Scene('fixture-scene', 'v1', (('o1',(shape.model_id,)),),
                       (s.SceneObject('o1',material,(shape,)),))

    def test_half_mm_floor_then_separate_arc_pose_and_numeric_errors(self):
        errors=s.ErrorBounds(F(1,10**6), F(1,10**5), F(1,10**7), F(1,10**6), F(1,10**6), 'fixture')
        sweep=self.sweep(end=(0,0,F(1,1000)), arc_length=F(1,750), curvature=F(1,2),
                         rotation=F(1,1500), errors=errors)
        self.assertEqual(F(1,2000),sweep.budget.rotation)
        self.assertEqual(F(1,9000000),sweep.budget.arc)
        self.assertEqual(F(13,2500000),sweep.budget.pose)
        self.assertEqual(F(1,2000)+F(1,9000000)+F(13,2500000)+F(31,10000000),sweep.budget.total)
        self.assertGreater(sweep.radius('full'),F(3,25)+F(1,2000))

    def test_larger_verified_rotation_is_not_clamped_to_floor(self):
        sweep=self.sweep(rotation=F(1,1000))
        self.assertEqual(F(13,25000),sweep.budget.rotation)

    def test_errors_have_no_implicit_zero_and_invalid_bounds_stop(self):
        with self.assertRaises(TypeError):s.ErrorBounds(position=0,pose_angle=0,asset=0,obstacle=0,source='fixture')
        for bad in (-1,float('inf'),float('nan'),True):
            with self.assertRaises((TypeError,ValueError)):s.ErrorBounds(0,0,bad,0,0,'fixture')
        with self.assertRaises(ValueError):s.ErrorBounds(0,0,0,0,0,'')
        with self.assertRaises(ValueError):self.sweep(arc_length=1)
        with self.assertRaises(ValueError):s.CapsuleModel('bad','v1',F(2,5),F(3,25),F(1,2))

    def test_snapshot_copies_all_nested_input_lists(self):
        q=[0,0,0,1];centre=[3,0,1];dims=[1,1,1]
        solid=self.shape(centre=centre,dimensions=dims,quaternion=q)
        sweep=self.sweep(quaternion=q)
        old=(solid.digest,sweep.digest,s.check_plane(sweep,solid,(1,0,0)))
        q[:]=[0,1,0,1];centre[0]=0;dims[0]=10
        self.assertEqual(old,(solid.digest,sweep.digest,s.check_plane(sweep,solid,(1,0,0))))
        with self.assertRaises(FrozenInstanceError):solid.kind='ellipsoid'

    def test_kind_rejects_mutable_string_subclass_before_geometry_sealing(self):
        class MutableKind(str):
            __hash__ = str.__hash__
            behaviour = 'box'
            def __eq__(self, other):
                return self.behaviour == other
        kind = MutableKind('box')
        with self.assertRaises(ValueError):self.shape(kind=kind)
        kind.behaviour = 'ellipsoid'
        with self.assertRaises(ValueError):self.shape(kind=kind)

    def test_material_rejects_alias_before_forbidden_union_policy(self):
        class MutableMaterial(str):
            __hash__ = str.__hash__
            drillable = False
            def __eq__(self, other):
                return str.__eq__(self, other) or (self.drillable and other == 'hard_rock')
        material = MutableMaterial('water')
        with self.assertRaises(ValueError):self.scene(material=material)
        material.drillable = True
        with self.assertRaises(ValueError):self.scene(material=material)

    def test_full_stage_cannot_alias_initial_at_any_certificate_entrypoint(self):
        class StageAlias(str):
            __hash__ = str.__hash__
            def __eq__(self, other):
                return other in ('initial', 'full')
        sweep, solid, stage = self.sweep(), self.shape(), StageAlias('full')
        certificate = s.check_plane(sweep, solid, (1,0,0))
        for call in (
            lambda:sweep.radius(stage), lambda:sweep.endpoints(stage),
            lambda:s.check_plane(sweep, solid, (1,0,0), stage=stage),
            lambda:s.separate(sweep, solid, stage=stage),
            lambda:s.recheck_certificate(certificate, sweep, solid, stage=stage),
        ):
            with self.assertRaises(ValueError):call()

    def test_strict_tangency_is_unknown_and_positive_gap_can_clear(self):
        sweep=self.sweep()
        tangent=self.shape(centre=(F(1241,2000),0,1),dimensions=(F(1,2),)*3)
        self.assertIsNone(s.check_plane(sweep,tangent,(1,0,0)))
        self.assertEqual('UNKNOWN',s.separate(sweep,tangent).status)
        apart=replace(tangent,centre=(F(1241,2000)+F(1,10**12),0,1))
        self.assertGreater(s.check_plane(sweep,apart,(1,0,0)).gap,0)

    def test_initial_overlap_is_checked_separately(self):
        scene=self.scene(self.shape(centre=(0,0,0)))
        result=s.certify_scene(self.sweep(),scene)
        self.assertEqual('UNKNOWN',result.status)
        self.assertEqual('initial',result.pairs[0].stage)
        self.assertFalse(result.motion_grant)

    def test_thin_layer_between_clear_endpoints_is_not_clear(self):
        sweep=self.sweep()
        layer=self.shape(centre=(0,0,1),dimensions=(1,1,F(1,10**8)))
        self.assertEqual('CLEAR',s.separate(sweep,layer,stage='initial').status)
        self.assertEqual('UNKNOWN',s.separate(sweep,layer).status)

    def test_tail_side_and_cap_contacts_are_not_point_queries(self):
        for centre in ((0,0,F(-1,2)),(F(1,10),0,1),(0,0,F(5,2))):
            with self.subTest(centre=centre):
                self.assertEqual('UNKNOWN',s.separate(self.sweep(),self.shape(centre=centre,dimensions=(F(1,100),)*3)).status)

    def test_casing_is_filled_cylinder_and_void_is_filled_ellipsoid(self):
        for kind in ('cylinder','ellipsoid'):
            self.assertEqual('UNKNOWN',s.separate(self.sweep(),self.shape(kind,(0,0,1),(1,2,3))).status)

    def test_scaled_polytope_and_rotated_nonuniform_shapes(self):
        vertices=tuple((x,y,z) for x in (-1,1) for y in (-1,1) for z in (-1,1))
        poly=self.shape('polytope',(.5,0,1),(10,F(1,10),F(1,10)),vertices=vertices)
        self.assertEqual('UNKNOWN',s.separate(self.sweep(),poly).status)
        for kind in ('box','ellipsoid','cylinder','polytope'):
            shape=self.shape(kind,(8,0,1),(1,2,3),quaternion=(4,-2,3,6),
                             vertices=vertices if kind=='polytope' else ())
            self.assertEqual('CLEAR',s.separate(self.sweep(),shape).status)

    def test_support_upper_matches_independent_precision160_analytic_formula(self):
        # q=(4,-2,3,6) has exact rotation Rx(atan(12/5))*Rz(atan(4/3)).
        matrix=((F(3,5),F(-4,5),0),(F(4,13),F(3,13),F(-12,13)),(F(48,65),F(36,65),F(5,13)))
        with localcontext() as ctx:
            ctx.prec=160
            dec=lambda f:Decimal(F(f).numerator)/Decimal(F(f).denominator)
            for kind in ('ellipsoid','cylinder'):
                shape=self.shape(kind,(1,2,3),(F(1,5),F(7,10),F(13,10)),quaternion=(4,-2,3,6))
                for n in ((3,4,5),(-7,2,11),(F(1,10**15),1,1)):
                    local=tuple(sum(matrix[i][j]*n[i] for i in range(3)) for j in range(3))
                    sq=tuple(dec(d*x)**2 for d,x in zip(shape.dimensions,local))
                    expected=sum(dec(a*b) for a,b in zip(shape.centre,n))
                    expected+=(sum(sq).sqrt() if kind=='ellipsoid' else (sq[0]+sq[1]).sqrt()+abs(dec(shape.dimensions[2]*local[2])))
                    self.assertGreaterEqual(dec(s.support_upper(shape,n)),expected-Decimal('1e-140'))

    def test_compound_free_channel_does_not_use_one_large_convex_hull(self):
        left=self.shape(centre=(-1,0,1),model_id='left')
        right=self.shape(centre=(1,0,1),model_id='right')
        scene=s.Scene('channel','v1',(('o',('left','right')),),
                      (s.SceneObject('o','water',(left,right)),))
        result=s.certify_scene(self.sweep(),scene)
        self.assertEqual('CLEAR',result.status)
        self.assertEqual(4,len(result.pairs))
        collided=replace(right,centre=(0,0,1))
        blocked=replace(scene,objects=(s.SceneObject('o','water',(left,collided)),))
        self.assertEqual('UNKNOWN',s.certify_scene(self.sweep(),blocked).status)

    def test_missing_duplicate_and_unexpected_object_or_piece_reject_whole_scene(self):
        solid=self.shape();obj=s.SceneObject('o','water',(solid,))
        for manifest,objects in (
            ((('o',('fixture-part',)),),()),
            ((('o',('fixture-part','missing')),),(obj,)),
            ((('o',('fixture-part','fixture-part')),),(obj,)),
            ((('o',('fixture-part',)),),(obj,obj)),
            ((),(obj,)),
            ((('o',('fixture-part',)),('o',('fixture-part',))),(obj,)),
        ):
            with self.subTest(manifest=manifest,objects=objects):
                with self.assertRaises(ValueError):s.Scene('bad','v1',manifest,objects)
        with self.assertRaises(ValueError):s.SceneObject('o','water',(solid,solid))

    def test_unsupported_shape_or_degenerate_piece_is_rejected_not_skipped(self):
        with self.assertRaises(ValueError):self.shape('visual-only-unknown')
        with self.assertRaises(ValueError):self.shape('polytope',vertices=((0,0,0),(1,0,0),(0,1,0),(1,1,0)))
        with self.assertRaises(TypeError):s.SceneObject('o','water',({'unsupported':'mesh'},))
        with self.assertRaises(ValueError):s.SceneObject('o','invented',(self.shape(),))

    def test_resource_limit_returns_unknown_without_dropping_objects(self):
        sweep=self.sweep();scene=self.scene()
        self.assertEqual('UNKNOWN',s.certify_scene(sweep,scene,limits=s.Limits(max_pairs=1)).status)
        self.assertEqual('UNKNOWN',s.separate(sweep,self.shape(),limits=s.Limits(max_normals=0)).status)
        vertices=tuple((x,y,z) for x in range(5) for y in range(5) for z in range(5))
        poly=self.shape('polytope',vertices=vertices)
        self.assertEqual(125,len(poly.vertices))
        self.assertEqual('UNKNOWN',s.separate(sweep,poly,limits=s.Limits(max_support_terms=1)).status)

    def test_wrong_axis_and_stale_cached_direction_cannot_make_clear(self):
        sweep=self.sweep();solid=self.shape()
        self.assertIsNone(s.check_plane(sweep,solid,(0,1,0)))
        self.assertIsNone(s.check_plane(sweep,solid,(0,0,0)))
        self.assertIsNone(s.check_plane(sweep,solid,(float('nan'),0,0)))
        cert=s.check_plane(sweep,solid,(1,0,0))
        colliding=replace(solid,centre=(0,0,1))
        self.assertFalse(s.recheck_certificate(cert,sweep,colliding))
        self.assertEqual('UNKNOWN',s.separate(sweep,colliding,cached_normals=((1,0,0),)).status)

    def test_certificate_binding_changes_with_every_geometry_budget_version_and_context(self):
        sweep=self.sweep();solid=self.shape()
        cert=s.check_plane(sweep,solid,(1,0,0),context='frozen-scene-hash')
        self.assertTrue(s.recheck_certificate(cert,sweep,solid,context='frozen-scene-hash'))
        for changed in (replace(solid,version='v2'),replace(solid,dimensions=(F(1,5),)*3)):
            self.assertFalse(s.recheck_certificate(cert,sweep,changed,context='frozen-scene-hash'))
        for changed in (replace(sweep,end=(0,0,1)),replace(sweep,errors=replace(self.errors,numeric=F(1,1000000))),
                        replace(sweep,model=replace(self.model,version='v2'))):
            self.assertFalse(s.recheck_certificate(cert,changed,solid,context='frozen-scene-hash'))
        self.assertFalse(s.recheck_certificate(cert,sweep,solid,context='other'))
        self.assertFalse(s.recheck_certificate(replace(cert,gap=cert.gap+1),sweep,solid,context='frozen-scene-hash'))
        self.assertFalse(cert.motion_grant)

    def test_certificate_hash_also_commits_the_proposed_normal(self):
        sweep=self.sweep();solid=self.shape()
        first=s.check_plane(sweep,solid,(1,0,0))
        second=s.check_plane(sweep,solid,(2,0,0))
        self.assertNotEqual(first.binding,second.binding)

    def test_forbidden_union_precedes_drillable_rock_and_rock_is_pending_law(self):
        rock=s.SceneObject('rock','hard_rock',(self.shape(centre=(0,0,1),model_id='rock-part'),))
        water=s.SceneObject('water','water',(self.shape(centre=(0,0,1),model_id='water-part'),))
        both=s.Scene('mix','v1',(('rock',('rock-part',)),('water',('water-part',))),(rock,water))
        self.assertEqual('UNKNOWN',s.certify_scene(self.sweep(),both).status)
        alone=s.Scene('rock','v1',(('rock',('rock-part',)),),(rock,))
        self.assertEqual('DRILLING_REQUIRED',s.certify_scene(self.sweep(),alone).status)
        superhard=replace(alone,objects=(replace(rock,superhard=True),))
        self.assertEqual('UNKNOWN',s.certify_scene(self.sweep(),superhard).status)
        self.assertNotEqual(both.digest,replace(both,version='v2').digest)

    def test_thirty_obstacles_allow_clear_complete_path_without_motion_grant(self):
        objects=tuple(s.SceneObject(str(i),'water',(self.shape(centre=(3+i%3,3+i//3,i%4),model_id=str(i)),)) for i in range(30))
        manifest=tuple((o.object_id,tuple(p.model_id for p in o.parts)) for o in objects)
        result=s.certify_scene(self.sweep(end=(0,0,F(1,1000)),arc_length=F(1,1000)),s.Scene('thirty','v1',manifest,objects))
        self.assertEqual('CLEAR',result.status)
        self.assertEqual(60,len(result.pairs))
        self.assertFalse(result.motion_grant)

    def test_exact_axis_aabb_oracle_never_false_clear_and_does_not_block_everything(self):
        rng=random.Random(20261016);sweep=self.sweep();radius=F(241,2000)
        clear=contact=0
        for _ in range(240):
            c=tuple(F(rng.randint(-2500,3500),1000) for _ in range(3))
            dims=tuple(F(rng.randint(1,500),1000) for _ in range(3))
            gaps=(max(F(0),abs(c[0])-dims[0]),max(F(0),abs(c[1])-dims[1]),
                  max(F(0),F(-2,5)-(c[2]+dims[2]),c[2]-dims[2]-F(12,5)))
            touching=sum(x*x for x in gaps)<=radius*radius
            result=s.separate(sweep,self.shape(centre=c,dimensions=dims))
            if touching:
                contact+=1;self.assertNotEqual('CLEAR',result.status)
            clear+=result.status=='CLEAR'
        self.assertGreater(contact,0)
        self.assertGreater(clear,200)

    def test_rotated_ellipsoid_and_cylinder_exact_side_tangency(self):
        matrix=((F(3,5),F(-4,5),0),(F(4,13),F(3,13),F(-12,13)),(F(48,65),F(36,65),F(5,13)))
        transform=lambda v:tuple(sum(a*b for a,b in zip(row,v)) for row in matrix)
        q=(4,-2,3,6);normal=transform((3,4,0));boundary=(F(16,15),F(9,20),0)
        for kind in ('ellipsoid','cylinder'):
            for delta in (F(-1,10**6),F(0),F(1,10**6)):
                centre=tuple(x+(F(241,2000)+delta)*n/5 for x,n in zip(boundary,(3,4,0)))
                sweep=self.sweep(start=transform(centre),end=transform(centre),arc_length=0,quaternion=q)
                solid=self.shape(kind,(0,0,0),(F(4,3),F(3,4),2),quaternion=q)
                cert=s.check_plane(sweep,solid,tuple(-n for n in normal))
                if delta>0:
                    self.assertIsNotNone(cert)
                    self.assertGreater(cert.gap,5*delta-F(1,10**25))
                else:
                    self.assertIsNone(cert)
                    self.assertNotEqual('CLEAR',s.separate(sweep,solid).status)

    def test_candidate_search_can_clear_nonuniform_side_with_one_mm_gap(self):
        boundary=(F(16,15),F(9,20),0)
        centre=tuple(x+(F(241,2000)+F(1,1000))*n/5 for x,n in zip(boundary,(3,4,0)))
        sweep=self.sweep(start=centre,end=centre,arc_length=0)
        for kind in ('ellipsoid','cylinder'):
            solid=self.shape(kind,(0,0,0),(F(4,3),F(3,4),2))
            self.assertEqual('CLEAR',s.separate(sweep,solid).status)

    def test_diagonal_sweep_does_not_replace_full_interval_with_endpoint_checks(self):
        sweep=self.sweep(end=(2,1,2),arc_length=3)
        solid=self.shape(centre=(1,F(1,2),1),dimensions=(F(1,10**6),)*3)
        self.assertEqual('CLEAR',s.separate(sweep,solid,stage='initial').status)
        end=self.sweep(start=(2,1,2),end=(2,1,2),arc_length=0)
        self.assertEqual('CLEAR',s.separate(end,solid,stage='initial').status)
        self.assertEqual('UNKNOWN',s.separate(sweep,solid).status)

    def test_arc_bound_uses_length_not_chord_in_sagitta_fixture(self):
        # Math fixture, not a legal product substep: unit arc sagitta=1/5.
        sweep=self.sweep(start=(F(-3,5),F(4,5),0),end=(F(3,5),F(4,5),0),
                         arc_length=F(13,10),curvature=1)
        self.assertEqual(F(169,800),sweep.budget.arc)
        self.assertGreater(sweep.budget.arc,F(1,5))
        solid=self.shape(centre=(0,F(28,25),0),dimensions=(F(1,10**6),)*3)
        self.assertEqual('UNKNOWN',s.separate(sweep,solid).status)
        self.assertEqual('CLEAR',s.separate(replace(sweep,curvature=0),solid).status)


if __name__=='__main__':
    unittest.main()
