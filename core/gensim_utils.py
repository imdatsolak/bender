# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

import numpy


def cosine(v1, v2):
    cos = numpy.dot(v1, v2)
    cos /= numpy.linalg.norm(v1)
    cos /= numpy.linalg.norm(v2)
    return cos


