
import numpy as np
from collections import deque, namedtuple
import _transformations as trans
from .utils import rotations as rotutils

# TODO: Check for loops and duplicate nodes in the Scene graph
class SceneNode(object):

    def __init__(self, parent=None, children=None):
        """A Node of the Scenegraph.  Has children, but no parent."""
        self._children = []
        self._parent = None
        if parent:
            self.parent = parent
        if children:
            self.add_children(children)

    def __iter__(self):
        """Returns an iterator that walks through the scene graph,
         starting with the current object."""
        def walk_tree_breadthfirst(obj):
            """tree walking algorithm, using algorithm from
            http://kmkeen.com/python-trees/"""
            order = deque([obj])
            while len(order) > 0:
                order.extend(order[0]._children)
                yield order.popleft()

        return walk_tree_breadthfirst(self)

    @property
    def parent(self):
        """A SceneNode object that is this object's parent in the scene graph."""
        return self._parent

    @parent.setter
    def parent(self, value):
        assert isinstance(value, SceneNode)
        if self._parent is not None:
            self._parent._children.remove(self)
        self._parent = value
        self._parent._children.append(self)

    def add_children(self, children=list()):
        """Adds a list of objects as children in the scene graph."""

        for child in children:
            assert isinstance(child, SceneNode)
            child._parent = self
            self._children.append(child)

    def remove_children(self, children):
        for child in children:
            child._parent = None
            self._children.remove(child)

    @property
    def children(self):
        return tuple(self._children)


class Physical(object):

    def __init__(self, position=(0., 0., 0.), rotation=(0., 0., 0.), scale=1.,
                 *args, **kwargs):
        """XYZ Position, Scale and XYZEuler Rotation Class.

        Args:
            position (list): (x, y, z) translation values.
            rotation (list): (x, y, z) rotation values
            scale (float): uniform scale factor. 1 = no scaling.
        """
        super(Physical, self).__init__(*args, **kwargs)

        self.rot = rotutils.RotationEulerDegrees(*rotation)
        self.pos = rotutils.Translation(*position)
        self.scale = scale

        self.model_matrix = np.zeros((4,4))
        self.normal_matrix = np.zeros((4,4))
        self.view_matrix = np.zeros((4,4))

        self.update()

    def update(self):
        """Calculate model, normal, and view matrices from position, rotation, and scale data."""
        self.model_matrix[:] = np.dot(self.pos.to_matrix(), self.rot.to_matrix())
        self.view_matrix[:] = trans.inverse_matrix(self.model_matrix)
        self.model_matrix[:] = np.dot(self.model_matrix, trans.scale_matrix(self.scale))
        self.normal_matrix[:] = trans.inverse_matrix(self.model_matrix.T)

    ##################################################################################################
    ### Methods below added for backwards compatibility.  Will be deprecated in the future.         ##
    ### Use self.rot and self.pos objects instead, which are more performant and have more features.##
    ##################################################################################################
    @property
    def rotation(self):
        return self.rot[:]

    @rotation.setter
    def rotation(self, value):
        self.rot[:] = value

    @property
    def rot_x(self):
        return self.rot.x

    @rot_x.setter
    def rot_x(self, value):
        self.rot.x = value

    @property
    def rot_y(self):
        return self.rot.y

    @rot_y.setter
    def rot_y(self, value):
        self.rot.y = value

    @property
    def rot_z(self):
        return self.rot.z

    @rot_z.setter
    def rot_z(self, value):
        self.rot.z = value

    @property
    def position(self):
        return self.pos[:]

    @position.setter
    def position(self, value):
        self.pos[:] = value

    @property
    def x(self):
        return self.pos.x

    @x.setter
    def x(self, value):
        self.pos.x = value

    @property
    def y(self):
        return self.pos.y

    @y.setter
    def y(self, value):
        self.pos.y = value

    @property
    def z(self):
        return self.pos.z

    @z.setter
    def z(self, value):
        self.pos.z = value


class PhysicalNode(Physical, SceneNode):

    def __init__(self, *args, **kwargs):
        """Object with xyz position and rotation properties that are relative to its parent."""
        self.model_matrix_global = np.zeros((4,4))
        self.normal_matrix_global = np.zeros((4,4))
        self.view_matrix_global = np.zeros((4,4))
        super(PhysicalNode, self).__init__(*args, **kwargs)

    def update(self):
        super(PhysicalNode, self).update()

        """Calculate world matrix values from the dot product of the parent."""
        if self.parent:
            self.model_matrix_global[:] = np.dot(self.parent.model_matrix_global, self.model_matrix)
            self.normal_matrix_global[:] = np.dot(self.parent.normal_matrix_global, self.normal_matrix)
            self.view_matrix_global[:] = np.dot(self.parent.normal_matrix_global, self.normal_matrix)
        else:
            self.model_matrix_global[:] = self.model_matrix
            self.normal_matrix_global[:] = self.normal_matrix
            self.view_matrix_global[:] = self.view_matrix

    @property
    def position_global(self):
        return tuple(self.model_matrix_global[:3, -1].tolist())
