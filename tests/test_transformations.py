try:
    from . import generic as g
except BaseException:
    import generic as g


class TransformTest(g.unittest.TestCase):

    def test_doctest(self):
        """
        Run doctests on transformations, which checks docstrings
        for interactive sessions and then verifies they execute
        correctly.

        This is how the upstream transformations unit tests,
        but it depends on numpy string formatting and is very
        flaky.
        """
        import trimesh
        import random
        import doctest

        # make sure formatting is the same as their docstrings
        g.np.set_printoptions(suppress=True, precision=5)

        # monkey patch import transformations with random for the examples
        trimesh.transformations.random = random

        # search for interactive sessions in docstrings and verify they work
        # they are super unreliable and depend on janky string formatting
        results = doctest.testmod(trimesh.transformations,
                                  verbose=False,
                                  raise_on_error=False)
        g.log.info('transformations {}'.format(str(results)))

    def test_downstream(self):
        """
        Run tests on functions that were added by us to the
        original transformations.py
        """
        tr = g.trimesh.transformations

        assert not tr.is_rigid(g.np.ones((4, 4)))

        planar = tr.planar_matrix(offset=[10, -10], theta=0.0)
        assert g.np.allclose(planar[:2, 2], [10, -10])

        planar = tr.planar_matrix(offset=[0, -0], theta=g.np.pi)
        assert g.np.allclose(planar[:2, 2], [0, 0])

        planar = tr.planar_matrix(offset=[0, 0], theta=0.0)
        assert g.np.allclose(planar, g.np.eye(3))

        as_3D = tr.planar_matrix_to_3D(g.np.eye(3))
        assert g.np.allclose(as_3D, g.np.eye(4))

        spherical = tr.spherical_matrix(theta=0.0, phi=0.0)
        assert g.np.allclose(spherical, g.np.eye(4))

        points = g.np.arange(60, dtype=g.np.float64).reshape((-1, 3))
        assert g.np.allclose(tr.transform_points(points, g.np.eye(4)), points)

        points = g.np.arange(60, dtype=g.np.float64).reshape((-1, 2))
        assert g.np.allclose(tr.transform_points(points, g.np.eye(3)), points)

    def test_around(self):
        # check transform_around on 2D points
        points = g.np.random.random((100, 2))
        for i, p in enumerate(points):
            offset = g.np.random.random(2)
            matrix = g.trimesh.transformations.planar_matrix(
                theta=g.np.random.random() + .1,
                offset=offset,
                point=p)

            # apply the matrix
            check = g.trimesh.transform_points(points, matrix)
            compare = g.np.isclose(check, points + offset)
            # the point we rotated around shouldn't move
            assert compare[i].all()
            # all other points should move
            assert compare.all(axis=1).sum() == 1

        # check transform_around on 3D points
        points = g.np.random.random((100, 3))
        for i, p in enumerate(points):
            matrix = g.trimesh.transformations.random_rotation_matrix()
            matrix = g.trimesh.transformations.transform_around(matrix, p)

            # apply the matrix
            check = g.trimesh.transform_points(points, matrix)
            compare = g.np.isclose(check, points)
            # the point we rotated around shouldn't move
            assert compare[i].all()
            # all other points should move
            assert compare.all(axis=1).sum() == 1

    def test_rotation(self):
        """
        test
        """
        rotation_matrix = g.trimesh.transformations.rotation_matrix

        R = rotation_matrix(g.np.pi / 2, [0, 0, 1], [1, 0, 0])
        assert g.np.allclose(g.np.dot(R,
                                      [0, 0, 0, 1]),
                             [1, -1, 0, 1])

        angle = (g.np.random.random() - 0.5) * (2 * g.np.pi)
        direc = g.np.random.random(3) - 0.5
        point = g.np.random.random(3) - 0.5
        R0 = rotation_matrix(angle, direc, point)
        R1 = rotation_matrix(angle - 2 * g.np.pi, direc, point)
        assert g.trimesh.transformations.is_same_transform(R0, R1)

        R0 = rotation_matrix(angle, direc, point)
        R1 = rotation_matrix(-angle, -direc, point)
        assert g.trimesh.transformations.is_same_transform(R0, R1)

        I = g.np.identity(4, g.np.float64)  # NOQA
        assert g.np.allclose(I, rotation_matrix(g.np.pi * 2, direc))

        assert g.np.allclose(
            2,
            g.np.trace(rotation_matrix(g.np.pi / 2,
                                       direc, point)))

        # test symbolic
        angle = g.sp.Symbol('angle')
        Rs = rotation_matrix(angle, [0, 0, 1], [1, 0, 0])

        R = g.np.array(Rs.subs(
            angle,
            g.np.pi / 2.0).evalf()).astype(g.np.float64)

        assert g.np.allclose(g.np.dot(R,
                                      [0, 0, 0, 1]),
                             [1, -1, 0, 1])

    def test_tiny(self):
        """
        Test transformations with models containing very small triangles
        """
        for validate in [False, True]:
            m = g.get_mesh('ADIS16480.STL', validate=validate)
            m.apply_scale(.001)
            m._cache.clear()
            fz = g.np.nonzero(g.np.linalg.norm(
                m.face_normals,
                axis=1) < 1e-3)
            print(fz)
            m.apply_transform(
                g.trimesh.transformations.rotation_matrix(
                    g.np.pi / 4, [0, 0, 1]))


if __name__ == '__main__':
    g.trimesh.util.attach_to_log()
    g.unittest.main()
