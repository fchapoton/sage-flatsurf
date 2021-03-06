from collections import deque, defaultdict

from flatsurf.geometry.tangent_bundle import *
from flatsurf.geometry.polygon import is_same_direction

# Vincent question:
# using deque has the disadvantage of losing the initial points
# ideally doig
#  my_line[i]
# we should always access to the same element

def get_linearity_coeff(u, v):
    r"""
    Given the two 2-dimensional vectors ``u`` and ``v``, return ``a`` so that
    ``v = a*u``

    If the vectors are not colinear, a ``ValueError`` is raised.

    EXAMPLES::

        sage: from flatsurf.geometry.straight_line_trajectory import get_linearity_coeff

        sage: V = VectorSpace(QQ,2)
        sage: get_linearity_coeff(V((1,0)), V((2,0)))
        2
        sage: get_linearity_coeff(V((2,0)), V((1,0)))
        1/2
        sage: get_linearity_coeff(V((0,1)), V((0,2)))
        2
        sage: get_linearity_coeff(V((0,2)), V((0,1)))
        1/2
        sage: get_linearity_coeff(V((1,2)), V((-2,-4)))
        -2

        sage: get_linearity_coeff(V((1,1)), V((-1,1)))
        Traceback (most recent call last):
        ...
        ValueError: non colinear
    """
    if u[0]:
        a = v[0]/u[0]
        if v[1] != a*u[1]:
            raise ValueError("non colinear")
        return a
    elif v[0]:
        raise ValueError("non colinear")
    elif u[1]:
        return v[1]/u[1]
    else:
        raise ValueError("zero vector")

class SegmentInPolygon:
    r"""
    Maximal segment in a polygon of a similarity surface

    EXAMPLES::

        sage: from flatsurf import *
        sage: from flatsurf.geometry.straight_line_trajectory import SegmentInPolygon
        sage: s = similarity_surfaces.example()
        sage: v = s.tangent_vector(0, (1/3,-1/4), (0,1))
        sage: SegmentInPolygon(v)
        Segment in polygon 0 starting at (1/3, -1/3) and ending at (1/3, 0)
    """
    def __init__(self, start, end=None):
        if not end is None:
            # WARNING: here we assume that both start and end are on the
            # boundary
            self._start = start
            self._end = end
        else:
            self._end = start.forward_to_polygon_boundary()
            self._start = self._end.forward_to_polygon_boundary()

    def __eq__(self, other):
        return type(self) is type(other) and \
               self._start == other._start and \
               self._end == other._end

    def __ne__(self, other):
        return type(self) is not type(other) or \
               self._start != other._start or \
               self._end != other._end

    def __repr__(self):
        r"""
        TESTS::

            sage: from flatsurf import *
            sage: from flatsurf.geometry.straight_line_trajectory import SegmentInPolygon
            sage: s = similarity_surfaces.example()
            sage: v = s.tangent_vector(0, (0,0), (3,-1))
            sage: SegmentInPolygon(v)
            Segment in polygon 0 starting at (0, 0) and ending at (2, -2/3)
        """
        return "Segment in polygon {} starting at {} and ending at {}".format(
                self.polygon_label(), self.start().point(), self.end().point())

    def start(self):
        r"""
        Return the tangent vector associated to the start of a trajectory pointed forward.
        """
        return self._start

    def start_is_singular(self):
        return self._start.is_based_at_singularity()

    def end(self):
        r"""
        Return a TangentVector associated to the end of a trajectory, pointed backward.
        """
        return self._end

    def end_is_singular(self):
        return self._end.is_based_at_singularity()

    def is_edge(self):
        if not self.start_is_singular() or not self.end_is_singular():
            return False
        vv=self.start().vector()
        vertex=self.start().singularity()
        ww=self.start().polygon().edge(vertex)
        from flatsurf.geometry.polygon import is_same_direction
        return is_same_direction(vv,ww)

    def edge(self):
        if not self.is_edge():
            raise ValueError("Segment asked for edge when not an edge")
        return self.start().singularity()

    def polygon_label(self):
        return self._start.polygon_label()

    def invert(self):
        return SegmentInPolygon(self._end, self._start)

    def next(self):
        r"""
        Return the next segment obtained by continuing straight through the end point.

        EXAMPLES::

            sage: from flatsurf import *
            sage: from flatsurf.geometry.straight_line_trajectory import SegmentInPolygon

            sage: s = similarity_surfaces.example()
            sage: s.polygon(0)
            Polygon: (0, 0), (2, -2), (2, 0)
            sage: s.polygon(1)
            Polygon: (0, 0), (2, 0), (1, 3)
            sage: v = s.tangent_vector(0, (0,0), (3,-1))
            sage: seg = SegmentInPolygon(v)
            sage: seg
            Segment in polygon 0 starting at (0, 0) and ending at (2, -2/3)
            sage: seg.next()
            Segment in polygon 1 starting at (2/3, 2) and ending at (14/9, 4/3)
        """
        if self.end_is_singular():
            raise ValueError("Cannot continue from singularity")
        return SegmentInPolygon(self._end.invert())

    def previous(self):
        if self.end_is_singular():
            raise ValueError("Cannot continue from singularity")
        return SegmentInPolygon(self._start.invert()).invert()


    # DEPRECATED STUFF THAT WILL BE REMOVED

    def start_point(self):
        from sage.misc.superseded import deprecation
        deprecation(1, "do not use start_point but start().point()")
        return self._start.point()

    def start_direction(self):
        from sage.misc.superseded import deprecation
        deprecation(1, "do not use start_direction but start().vector()")
        return self._start.vector()

    def end_point(self):
        from sage.misc.superseded import deprecation
        deprecation(1, "do not use end_point but end().point()")
        return self._end.point()

    def end_direction(self):
        from sage.misc.superseded import deprecation
        deprecation(1, "do not use end_direction but end().vector()")
        return self._end.vector()

class AbstractStraightLineTrajectory:
    r"""
    You need to implement:

    - ``def segment(self, i)``
    - ``def segments(self)``
    """
    def __repr__(self):
        start = self.segment(0).start()
        end = self.segment(-1).end()
        return "Straight line trajectory made of {} segments from {} in polygon {} to {} in polygon {}".format(
                self.combinatorial_length(),
                start.point(), start.polygon_label(),
                end.point(), end.polygon_label())

    def graphical_trajectory(self, graphical_surface):
        r"""
        Returns a ``GraphicalStraightLineTrajectory`` corresponding to this
        trajectory in the provided  ``GraphicalSurface``.
        """
        from flatsurf.graphical.straight_line_trajectory import GraphicalStraightLineTrajectory
        return GraphicalStraightLineTrajectory(graphical_surface, self)

    def coding(self, alphabet=None):
        r"""
        Return the coding of this trajectory with respect to the sides of the
        polygons

        INPUT:

        - ``alphabet`` -- an optional dictionary ``(lab,nb) -> letter``. If some
          labels are avoided then these crossings are ignored.

        EXAMPLES::

            sage: from flatsurf import *
            sage: t = translation_surfaces.square_torus()

            sage: v = t.tangent_vector(0, (1/2,0), (5,6))
            sage: l = v.straight_line_trajectory()
            sage: alphabet = {(0,0): 'a', (0,1): 'b', (0,2):'a', (0,3): 'b'}
            sage: l.coding()
            [(0, 0), (0, 1)]
            sage: l.coding(alphabet)
            ['a', 'b']
            sage: l.flow(10); l.flow(-10)
            sage: l.coding()
            [(0, 2), (0, 1), (0, 2), (0, 1), (0, 2), (0, 1), (0, 2), (0, 1), (0, 2)]
            sage: print ''.join(l.coding(alphabet))
            ababababa

            sage: v = t.tangent_vector(0, (1/2,0), (7,13))
            sage: l = v.straight_line_trajectory()
            sage: l.flow(10); l.flow(-10)
            sage: print ''.join(l.coding(alphabet))
            aabaabaababaabaabaab

        For a closed trajectory, the last label (corresponding also to the
        starting point) is not considered::

            sage: v = t.tangent_vector(0, (1/5,1/7), (1,1))
            sage: l = v.straight_line_trajectory()
            sage: l.flow(10)
            sage: l.is_closed()
            True
            sage: l.coding(alphabet)
            ['a', 'b']

        Check that the saddle connections that are obtained in the torus get the
        expected coding::

            sage: for _ in range(10):
            ....:     x = ZZ.random_element(1,30)
            ....:     y = ZZ.random_element(1,30)
            ....:     x,y = x/gcd(x,y), y/gcd(x,y)
            ....:     v = t.tangent_vector(0, (0,0), (x,y))
            ....:     l = v.straight_line_trajectory()
            ....:     l.flow(200); l.flow(-200)
            ....:     w = ''.join(l.coding(alphabet))
            ....:     assert Word(w+'ab'+w).is_balanced()
            ....:     assert Word(w+'ba'+w).is_balanced()
            ....:     assert w.count('a') == y-1
            ....:     assert w.count('b') == x-1
        """
        ans = []

        s = self._segments[0]
        start = s.start()
        if start._position._position_type == start._position.EDGE_INTERIOR:
            p = s.polygon_label()
            e = start._position.get_edge()
            lab = (p,e) if alphabet is None else alphabet.get((p,e))
            if lab is not None:
                ans.append(lab)

        for i in range(len(self._segments)-1):
            s = self._segments[i]
            end = s.end()
            p = s.polygon_label()
            e = end._position.get_edge()
            lab = (p,e) if alphabet is None else alphabet.get((p,e))
            if lab is not None:
                ans.append(lab)

        s = self._segments[-1]
        end = s.end()
        if end._position._position_type == end._position.EDGE_INTERIOR and \
           end.invert() != start:
            p = s.polygon_label()
            e = end._position.get_edge()
            lab = (p,e) if alphabet is None else alphabet.get((p,e))
            if lab is not None:
                ans.append(lab)

        return ans

class StraightLineTrajectory(AbstractStraightLineTrajectory):
    r"""
    Straight-line trajectory in a similarity surface.
    """
    def __init__(self, tangent_vector):
        self._segments = deque()
        seg = SegmentInPolygon(tangent_vector)
        self._segments.append(seg)
        self._setup_forward()
        self._setup_backward()

    def segment(self, i):
        r"""
        EXAMPLES::

            sage: from flatsurf import *

            sage: O = translation_surfaces.regular_octagon()
            sage: v = O.tangent_vector(0, (1,1), (33,45))
            sage: L = v.straight_line_trajectory()
            sage: L.segment(0)
            Segment in polygon 0 starting at (4/15, 0) and ending at (11/26*a +
            1, 15/26*a + 1)
            sage: L.flow(-1)
            sage: L.segment(0)
            Segment in polygon 0 starting at (-1/2*a, 7/22*a + 7/11) and ending
            at (4/15, a + 1)
            sage: L.flow(1)
            sage: L.segment(2)
            Segment in polygon 0 starting at (-1/13*a, 1/13*a) and ending at
            (9/26*a + 11/13, 17/26*a + 15/13)
        """
        return self.segments()[i]

    def combinatorial_length(self):
        return len(self.segments())

    def segments(self):
        return self._segments

    def _setup_forward(self):
        v = self.terminal_tangent_vector()
        if v.is_based_at_singularity():
            self._forward = None
        else:
            self._forward = v.invert()

    def _setup_backward(self):
        v = self.initial_tangent_vector()
        if v.is_based_at_singularity():
            self._backward = None
        else:
            self._backward = v.invert()

    def initial_tangent_vector(self):
        return self._segments[0].start()

    def terminal_tangent_vector(self):
        return self._segments[-1].end()

    def is_forward_separatrix(self):
        return self._forward is None

    def is_backward_separatrix(self):
        return self._backward is None

    def is_saddle_connection(self):
        return (self._forward is None) and (self._backward is None)

    def is_closed(self):
        r"""
        Test whether this is a closed trajectory.

        By convention, by a closed trajectory we mean a trajectory without any
        singularities.

        .. SEEALSO::

            :meth:`is_saddle_connection`

        EXAMPLES:

        An example in the torus::

            sage: from flatsurf import *
            sage: p = polygons.square()
            sage: t = similarity_surfaces([p], {(0,0):(0,3), (0,1):(0,2)})

            sage: v = t.tangent_vector(0, (1/2,0), (1/3,7/5))
            sage: l = v.straight_line_trajectory()
            sage: l.is_closed()
            False
            sage: l.flow(100)
            sage: l.is_closed()
            True

            sage: v = t.tangent_vector(0, (1/2,0), (1/3,2/5))
            sage: l = v.straight_line_trajectory()
            sage: l.flow(100)
            sage: l.is_closed()
            False
            sage: l.is_saddle_connection()
            False
            sage: l.flow(-100)
            sage: l.is_saddle_connection()
            True
        """
        return (not self.is_forward_separatrix()) and \
            self._forward.differs_by_scaling(self.initial_tangent_vector())

    def flow(self, steps):
        r"""
        Append or preprend segments to the trajectory.
        If steps is positive, attempt to append this many segments.
        If steps is negative, attempt to prepend this many segments.
        Will fail gracefully the trajectory hits a singularity or closes up.

        EXAMPLES::

            sage: from flatsurf import *

            sage: s = similarity_surfaces.example()
            sage: v = s.tangent_vector(0, (1,-1/2), (3,-1))
            sage: traj = v.straight_line_trajectory()
            sage: traj
            Straight line trajectory made of 1 segments from (1/4, -1/4) in polygon 0 to (2, -5/6) in polygon 0
            sage: traj.flow(1)
            sage: traj
            Straight line trajectory made of 2 segments from (1/4, -1/4) in polygon 0 to (61/36, 11/12) in polygon 1
            sage: traj.flow(-1)
            sage: traj
            Straight line trajectory made of 3 segments from (15/16, 45/16) in polygon 1 to (61/36, 11/12) in polygon 1
        """
        while steps>0 and \
            (not self.is_forward_separatrix()) and \
            (not self.is_closed()):
                self._segments.append(SegmentInPolygon(self._forward))
                self._setup_forward()
                steps -= 1
        while steps<0 and \
            (not self.is_backward_separatrix()) and \
            (not self.is_closed()):
                self._segments.appendleft(SegmentInPolygon(self._backward).invert())
                self._setup_backward()
                steps += 1

    # DEPRECATED STUFF

    def initial_segment(self):
        from sage.misc.superseded import deprecation
        deprecation(-1, "initial_segment is deprecated... use self.segments()[0]")
        return self._segments[0]

    def terminal_segment(self):
        from sage.misc.superseded import deprecation
        deprecation(-1, "terminal_segment is deprecated... use self.segments()[0]")
        return self._segments[-1]

class StraightLineTrajectoryTranslation(AbstractStraightLineTrajectory):
    r"""
    Straight line trajectory in a translation surface.

    This is similar to :class:`StraightLineTrajectory` but implemented using
    interval exchange maps. It should be faster than the implementation via
    segments and flowing in polygons.

    Though, there is one big difference, this class can model an edge!

    This class only stores a list of triples ``(p, e, x)`` where:
    
    - ``p`` is a label of a polygon
    
    - ``e`` is the number of some edge in ``p``

    - ``x`` is the position of the point in ``e`` (be careful that it is not
      necessarily a number between 0 and 1. It is given relatively to the length
      of the induced interval in the iet)

    (see the methods :meth:`_prev` and :meth:`_next`)
    """
    def __init__(self, tangent_vector):
        t = tangent_vector.polygon_label()
        self._vector = tangent_vector.vector()
        self._s = tangent_vector.surface()

        start = SegmentInPolygon(tangent_vector).start()
        pos = start._position
        if pos._position_type == pos.EDGE_INTERIOR:
            i = pos.get_edge()
        elif pos._position_type == pos.VERTEX:
            i = pos.get_vertex()
        else:
            raise RuntimeError("PROBLEM!")

        p = start.polygon_label()
        poly = self._s.polygon(p)

        T = self._get_iet(p)
        x = get_linearity_coeff(poly.vertex(i+1) - poly.vertex(i),
                                start.point() - poly.vertex(i))
        x *= T.length_bot(i)

        self._points = deque() # we store triples (lab, edge, rel_pos)
        self._points.append((p, i, x))

    def _next(self, p, e, x):
        r"""
        Return the image of ``(p, e, x)``

        EXAMPLES::

            sage: from flatsurf import *
            sage: from flatsurf.geometry.straight_line_trajectory import StraightLineTrajectoryTranslation
            sage: S = SymmetricGroup(3)
            sage: r = S('(1,2)')
            sage: u = S('(1,3)')
            sage: o = translation_surfaces.origami(r,u)
            sage: v = o.tangent_vector(1, (1/3,1/7), (5,13))
            sage: L = StraightLineTrajectoryTranslation(v)
            sage: t0 = (1,0,1/3)
            sage: t1 = L._next(*t0)
            sage: t2 = L._next(*t1)
            sage: t0,t1,t2
            ((1, 0, 1/3), (3, 0, 16/3), (1, 0, 31/3))
            sage: assert L._previous(*t2) == t1
            sage: assert L._previous(*t1) == t0
        """
        e, x = self._get_iet(p).forward_image(e, x)
        p, e = self._s.opposite_edge(p, e)
        return (p, e, x)

    def _previous(self, p, e, x):
        r"""
        Return the preimage of ``(p, e, x)``
        """
        p, e = self._s.opposite_edge(p, e)
        e, x = self._get_iet(p).backward_image(e, x)
        return (p, e, x)

    def combinatorial_length(self):
        return len(self._points)

    def _get_iet(self, label):
        polygon = self._s.polygon(label)
        try:
            return self._iets[polygon]
        except AttributeError:
            self._iets = {polygon: polygon.flow_map(self._vector)}
        except KeyError:
            self._iets[polygon] = polygon.flow_map(self._vector)
        return self._iets[polygon]

    def segment(self, i):
        r"""
        EXAMPLES::

            sage: from flatsurf import *
            sage: from flatsurf.geometry.straight_line_trajectory import StraightLineTrajectoryTranslation

            sage: O = translation_surfaces.regular_octagon()
            sage: v = O.tangent_vector(0, (1,1), (33,45))
            sage: L = StraightLineTrajectoryTranslation(v)
            sage: L.segment(0)
            Segment in polygon 0 starting at (4/15, 0) and ending at (11/26*a +
            1, 15/26*a + 1)
            sage: L.flow(-1)
            sage: L.segment(0)
            Segment in polygon 0 starting at (-1/2*a, 7/22*a + 7/11) and ending
            at (4/15, a + 1)
            sage: L.flow(1)
            sage: L.segment(2)
            Segment in polygon 0 starting at (-1/13*a, 1/13*a) and ending at
            (9/26*a + 11/13, 17/26*a + 15/13)
        """
        lab, e0, x0 = self._points[i]
        iet = self._get_iet(lab)
        e1, x1 = iet.forward_image(e0, x0)
        poly = self._s.polygon(lab)

        l0 = iet.length_bot(e0)
        l1 = iet.length_top(e1)

        point0 = poly.vertex(e0) + poly.edge(e0) * x0/l0
        point1 = poly.vertex(e1) + poly.edge(e1) * (l1-x1)/l1
        v0 = self._s.tangent_vector(lab, point0, self._vector)
        v1 = self._s.tangent_vector(lab, point1, -self._vector)
        return SegmentInPolygon(v0,v1)

    def segments(self):
        return [self.segment(i) for i in self.combinatorial_length()]

    def is_closed(self):
        return self._points[0] == self._next(*self._points[-1])

    def is_forward_separatrix(self):
        p1,e1,x1 = self._next(*self._points[-1])
        return x1.is_zero()

    def is_backward_separatrix(self):
        return self._points[0][2].is_zero()

    def is_saddle_connection(self):
        r"""
        EXAMPLES::

            sage: from flatsurf import *
            sage: from flatsurf.geometry.straight_line_trajectory import StraightLineTrajectoryTranslation

            sage: torus = translation_surfaces.square_torus()
            sage: v = torus.tangent_vector(0, (1/2,1/2), (1,1))
            sage: S = StraightLineTrajectoryTranslation(v)
            sage: S.is_saddle_connection()
            True

            sage: v = torus.tangent_vector(0, (1/3,2/3), (1,2))
            sage: S = StraightLineTrajectoryTranslation(v)
            sage: S.is_saddle_connection()
            False
            sage: S.flow(1)
            sage: S.is_saddle_connection()
            True
        """
        return self.is_forward_separatrix() and self.is_backward_separatrix() 

    def flow(self, steps):
        if steps > 0:
            t = self._points[-1]
            for i in range(steps):
                t = self._next(*t)
                if t == self._points[0] or t[2].is_zero():
                    break
                self._points.append(t)
        elif steps < 0:
            t = self._points[0]
            for i in range(-steps):
                if t[2].is_zero():
                    break
                t = self._previous(*t)
                if t == self._points[-1]:
                    # closed curve or backward separatrix
                    break
                self._points.appendleft(t)
