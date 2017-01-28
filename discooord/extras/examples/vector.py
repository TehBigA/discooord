import math


class Vector(object):
    x = None
    y = None
    z = None

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return Vector(
            self.y * other.z - other.y * self.z,
            self.z * other.x - other.z * self.x,
            self.y * other.y - other.y * self.y
        )

    def length_sq(self):
        return math.pow(self.x, 2) + math.pow(self.y, 2) + math.pow(self.z, 2)

    def length(self):
        return math.sqrt(self.length_sq())

    def normalize(self):
        len = self.length()
        self.x /= len
        self.y /= len
        self.z /= len
        return self

    def normal(self):
        len = self.length()
        return Vector(
            self.x / len,
            self.y / len,
            self.z / len
        )

    def __mul__(self, other):
        if isinstance(other, (int, long, float)):
            return Vector(
                self.x * other,
                self.y * other,
                self.z * other
            )
        elif isinstance(other, Vector):
            return Vector(
                self.x * other.x,
                self.y * other.y,
                self.z * other.z
            )

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        if isinstance(other, (int, long, float)):
            return Vector(
                self.x / other,
                self.y / other,
                self.z / other
            )
        elif isinstance(other, Vector):
            return Vector(
                self.x / other.x,
                self.y / other.y,
                self.z / other.z
            )

    def __add__(self, other):
        if isinstance(other, (int, long, float)):
            return Vector(
                self.x + other,
                self.y + other,
                self.z + other
            )
        elif isinstance(other, Vector):
            return Vector(
                self.x + other.x,
                self.y + other.y,
                self.z + other.z
            )

    def __sub__(self, other):
        if isinstance(other, (int, long, float)):
            return Vector(
                self.x - other,
                self.y - other,
                self.z - other
            )
        elif isinstance(other, Vector):
            return Vector(
                self.x - other.x,
                self.y - other.y,
                self.z - other.z
            )

    def __abs__(self):
        return Vector(
            abs(self.x),
            abs(self.y),
            abs(self.z)
        )

    def __neg__(self):
        return Vector(
            -self.x,
            -self.y,
            -self.z
        )

    def __getitem__(self, key):
        if key in (0, 'x'):
            return self.x
        elif key in (1, 'y'):
            return self.y
        elif key in (2, 'z'):
            return self.z
        raise IndexError('index out of range')

    def __setitem__(self, key, value):
        if key in (0, 'x'):
            self.x = value
        elif key in (1, 'y'):
            self.y = value
        elif key in (2, 'z'):
            self.z = value
        raise IndexError('index out of range')

    def __repr__(self):
        return '({}, {}, {})'.format(self.x, self.y, self.z)

    __len__ = length
