r"""Mappings between translation surfaces."""

from flatsurf.geometry.polygon import Polygons, wedge_product


class SimilaritySurfaceMapping:
    r"""Abstract class for any mapping between similarity surfaces."""
    
    def __init__(self, domain, codomain):
        self._domain=domain
        self._codomain=codomain
    
    def domain(self):
        r"""
        Return the domain of the mapping.
        """
        return self._domain

    def codomain(self):
        r"""
        Return the range of the mapping.
        """
        return self._codomain

    def push_vector_forward(self,tangent_vector):
        r"""Applies the mapping to the provided vector."""
        raise NotImplementedError

    def pull_vector_back(self,tangent_vector):
        r"""Applies the inverse of the mapping to the provided vector."""
        raise NotImplementedError

class SimilarityJoinPolygonsMapping(SimilaritySurfaceMapping):
    r"""
    Return a SimilaritySurfaceMapping joining two polygons together along the edge provided to the constructor.

    EXAMPLES::
    sage: from flatsurf.geometry.polygon import Polygons
    sage: p=Polygons(QQ)([(2,0),(-1,1),(-1,-1)])
    sage: from flatsurf.geometry.similarity_surface import SimilaritySurface_polygons_and_gluings
    sage: s=SimilaritySurface_polygons_and_gluings([p,p],[((0,0),(1,2)),((0,1),(1,0)),((0,2),(1,1))])
    sage: gs=s.graphical_surface()
    sage: gs.make_adjacent_and_visible(0,1)
    sage: gs.plot()
    sage: from flatsurf.geometry.mappings import SimilarityJoinPolygonsMapping
    sage: m = SimilarityJoinPolygonsMapping(s,0,1)
    [((0, 0), (0, 2)), ((0, 1), (0, 3)), ((0, 2), (0, 0)), ((0, 3), (0, 1))]
    sage: s2=m.codomain()
    sage: s2.graphical_surface().plot()
    sage: v=s.tangent_vector(1,(1,1/2),(1,2))
    sage: traj=v.straight_line_trajectory()
    sage: gs.plot()+traj.graphical_trajectory(gs).plot()
    sage: gs2=s2
    sage: gs2=s2.graphical_surface()
    sage: v2=m.push_vector_forward(v)
    sage: traj2=v2.straight_line_trajectory()
    sage: gs2.plot()+traj2.graphical_trajectory(gs2).plot()
    sage: s2.polygon(0)
    Polygon: (0, 0), (2, 0), (2, 1), (1, 1)
    sage: w2=s2.tangent_vector(0,(3/2,2/3),(1,1))
    sage: traj2=w2.straight_line_trajectory()
    sage: gs2.plot()+traj2.graphical_trajectory(gs2).plot()
    sage: w=m.pull_vector_back(w2)
    sage: traj=w.straight_line_trajectory()
    sage: gs.plot()+traj.graphical_trajectory(gs).plot()
    """
    def __init__(self, s, p1, e1):
        r"""
        Join polygon with label p1 of s to polygon sharing edge e1.
        """
        poly1=s.polygon(p1)
        p2,e2 = s.opposite_edge(p1,e1)
        poly2=s.polygon(p2)
        t=s.edge_transformation(p2, e2)
        dt=t.derivative()
        vs = []
        edge_map={} # Store the pairs for the old edges.
        for i in range(e1):
            edge_map[len(vs)]=(p1,i)
            vs.append(poly1.edge(i))
        ne=poly2.num_edges()
        for i in range(1,ne):
            ee=(e2+i)%ne
            edge_map[len(vs)]=(p2,ee)
            vs.append(dt * poly2.edge( ee ))
        for i in range(e1+1, poly1.num_edges()):
            edge_map[len(vs)]=(p1,i)
            vs.append(poly1.edge(i))
        
        inv_edge_map={}
        for key, value in edge_map.iteritems():
            inv_edge_map[value]=(p1,key)
        
        newpoly = Polygons(s.base_ring())(vs)
        
        if s.is_finite():
            # Finite surface. Use a dictionary for polygons
            polygons={}
            for label in s.polygon_labels():
                if label==p1:
                    polygons[label]=newpoly
                elif label != p2:
                    polygons[label]=s.polygon(label)
            gluings=[]
            # Iterate over the new edges:
            for ll1,pp1 in polygons.iteritems():
                for ee1 in range(pp1.num_edges()):
                    if ll1 == p1:
                        ll2,ee2 = edge_map[ee1]
                    else:
                        ll2,ee2 = (ll1,ee1)
                    ll3,ee3=s.opposite_edge(ll2,ee2)
                    if ll3 == p1 or ll3 == p2:
                        gluings.append( ( (ll1,ee1), inv_edge_map[(ll3,ee3)] ) )
                    else:
                        gluings.append( ( (ll1,ee1), (ll3,ee3) ) )
            from flatsurf.geometry.similarity_surface import SimilaritySurface_polygons_and_gluings
            s2=SimilaritySurface_polygons_and_gluings(polygons,gluings)
        else:
            # There is no reason this could not be implemented.
            raise NotImplementedError
        self._saved_label=p1
        self._removed_label=p2
        self._remove_map = t
        self._remove_map_derivative = dt
        self._glued_edge=e1
        SimilaritySurfaceMapping.__init__(self, s, s2)

    def push_vector_forward(self,tangent_vector):
        r"""Applies the mapping to the provided vector."""
        ring = tangent_vector.bundle().base_ring()
        if tangent_vector.polygon_label() == self._removed_label:
            return self._codomain.tangent_vector( \
                self._saved_label, \
                self._remove_map(tangent_vector.point()), \
                self._remove_map_derivative*tangent_vector.vector(), \
                ring = ring)
        else:
            return self._codomain.tangent_vector( \
                tangent_vector.polygon_label(), \
                tangent_vector.point(), \
                tangent_vector.vector(), \
                ring = ring)

    def pull_vector_back(self,tangent_vector):
        r"""
        Applies the inverse of the mapping to the provided vector.
        """
        ring = tangent_vector.bundle().base_ring()
        if tangent_vector.polygon_label() == self._saved_label:
            p=tangent_vector.point()
            v=self._domain.polygon(self._saved_label).vertex(self._glued_edge)
            e=self._domain.polygon(self._saved_label).edge(self._glued_edge)
            from flatsurf.geometry.polygon import wedge_product
            wp = wedge_product(p-v,e)
            if wp > 0:
                # in polygon with the removed label
                return self.domain().tangent_vector( \
                    self._removed_label, \
                    (~ self._remove_map)(tangent_vector.point()), \
                    (~ self._remove_map_derivative)*tangent_vector.vector(), \
                    ring = ring)
            if wp < 0:
                # in polygon with the removed label
                return self.domain().tangent_vector( \
                    self._saved_label, \
                    tangent_vector.point(), \
                    tangent_vector.vector(), \
                    ring = ring)
            # Otherwise wp==0
            w = tangent_vector.vector()
            wp = wedge_product(w,e)
            if wp > 0:
                # in polygon with the removed label
                return self.domain().tangent_vector( \
                    self._removed_label, \
                    (~ self._remove_map)(tangent_vector.point()), \
                    (~ self._remove_map_derivative)*tangent_vector.vector(), \
                    ring = ring)
            return self.domain().tangent_vector( \
                self._saved_label, \
                tangent_vector.point(), \
                tangent_vector.vector(), \
                ring = ring)
        else:
            return self._domain.tangent_vector( \
                tangent_vector.polygon_label(), \
                tangent_vector.point(), \
                tangent_vector.vector(), \
                ring = ring)

class SimilaritySplitPolygonsMapping(SimilaritySurfaceMapping):
    def __init__(self, s, p, v1, v2):
        r"""
        Split the polygon with label p of surface s along the diagonal joining vertex v1 to vertex v2.
        """
        poly=s.polygon(p)
        ne=poly.num_edges()
        if v1<0 or v2<0 or v1>=ne or v2>=ne:
            raise ValueError('Provided vertices out of bounds.')
        if abs(v1-v2)<=1 or abs(v1-v2)>=ne-1:
            raise ValueError('Provided diagonal is not a diagonal.')
        if v2<v1:
            temp=v1
            v1=v2
            v2=temp
            
        newvertices1=[poly.vertex(v2)-poly.vertex(v1)]
        for i in range(v2, v1+ne):
            newvertices1.append(poly.edge(i))
        newpoly1 = Polygons(s.base_ring())(newvertices1)
        
        newvertices2=[poly.vertex(v1)-poly.vertex(v2)]
        for i in range(v1,v2):
            newvertices2.append(poly.edge(i))
        newpoly2 = Polygons(s.base_ring())(newvertices2)

        if not s.is_finite():
            raise NotImplementedError

        polygon_map={}
        for label in s.polygon_labels():
            if label == p:
                polygon_map[label]=newpoly1
            else:
                polygon_map[label]=s.polygon(label)
        success=False
        
        new_label=len(polygon_map)
        # The following crap is to ensure that the new_label is not already in the dictionary by some fluke.
        while polygon_map.has_key(new_label):
            new_label=new_label+1
        polygon_map[new_label]=newpoly2
        
        old_to_new_labels={}
        for i in range(ne):
            if i<v1:
                old_to_new_labels[i]=(p,i+ne-v2+1)
            elif i<v2:
                old_to_new_labels[i]=(new_label,i-v1+1)
            else: # i>=v2
                old_to_new_labels[i]=(p,i-v2+1)
        new_to_old_labels={}
        for i,pair in old_to_new_labels.iteritems():
            new_to_old_labels[pair]=i
        
        gluings=[]
        # Iterate over the new edges:
        for l1,p1 in polygon_map.iteritems():
            for e1 in range(p1.num_edges()):
                if l1==p:
                    if e1==0:
                        # Special case, this is the cut
                        gluings.append( ( (p,0),(new_label,0) ) )
                        continue
                    l2=p
                    e2=new_to_old_labels[(p,e1)]
                elif l1==new_label:
                    if e1==0:
                        # Special case, this is the cut
                        gluings.append( ( (new_label,0),(p,0) ) )
                        continue
                    l2=p
                    e2=new_to_old_labels[(new_label,e1)]
                else:
                    l2=l1
                    e2=e1
                l3,e3 = s.opposite_edge(l2,e2)
                if l3==p:
                    l4,e4=old_to_new_labels[e3]
                else:
                    l4=l3
                    e4=e3
                gluings.append( ( (l1,e1), (l4,e4) ) )
        from flatsurf.geometry.similarity_surface import SimilaritySurface_polygons_and_gluings
        s2=SimilaritySurface_polygons_and_gluings(polygon_map,gluings)

        self._p=p
        self._v1=v1
        self._v2=v2
        self._new_label=new_label
        from flatsurf.geometry.translation import TranslationGroup
        TG=TranslationGroup(s.base_ring())
        self._tp = TG(-s.polygon(p).vertex(v1))
        self._tnew_label = TG(-s.polygon(p).vertex(v2))
        SimilaritySurfaceMapping.__init__(self, s, s2)

    def push_vector_forward(self,tangent_vector):
        r"""Applies the mapping to the provided vector."""
        ring = tangent_vector.bundle().base_ring()
        if tangent_vector.polygon_label() == self._p:
            point=tangent_vector.point()
            vertex1=self._domain.polygon(self._p).vertex(self._v1)
            vertex2=self._domain.polygon(self._p).vertex(self._v2)

            wp = wedge_product(vertex2-vertex1,point-vertex1)

            if wp > 0:
                # in new polygon 1
                return self.codomain().tangent_vector( \
                    self._p, \
                    self._tp(tangent_vector.point()), \
                    tangent_vector.vector(), \
                    ring = ring)
            if wp < 0:
                # in new polygon 2
                return self.codomain().tangent_vector( \
                    self._new_label, \
                    self._tnew_label(tangent_vector.point()), \
                    tangent_vector.vector(), \
                    ring = ring)

            # Otherwise wp==0
            w = tangent_vector.vector()
            wp = wedge_product(vertex2-vertex1,w)
            if wp > 0:
                # in new polygon 1
                return self.codomain().tangent_vector( \
                    self._p, \
                    self._tp(tangent_vector.point()), \
                    tangent_vector.vector(), \
                    ring = ring)
            # in new polygon 2
            return self.codomain().tangent_vector( \
                self._new_label, \
                self._tnew_label(tangent_vector.point()), \
                tangent_vector.vector(), \
                ring = ring)
        else:
            # Not in a polygon that was changed. Just copy the data.
            return self._codomain.tangent_vector( \
                tangent_vector.polygon_label(), \
                tangent_vector.point(), \
                tangent_vector.vector(), \
                ring = ring)


    def pull_vector_back(self,tangent_vector):
        r"""Applies the pullback mapping to the provided vector."""
        ring = tangent_vector.bundle().base_ring()
        if tangent_vector.polygon_label() == self._p:
            return self._domain.tangent_vector( \
                self._p, \
                (~ self._tp)(tangent_vector.point()), \
                tangent_vector.vector(), \
                ring = ring)
        elif tangent_vector.polygon_label() == self._new_label:
            return self._domain.tangent_vector( \
                self._p, \
                (~ self._tnew_label)(tangent_vector.point()), \
                tangent_vector.vector(), \
                ring = ring)
        else:
            # Not in a polygon that was changed. Just copy the data.
            return self._domain.tangent_vector( \
                self._p, \
                tangent_vector.point(), \
                tangent_vector.vector(), \
                ring = ring)


