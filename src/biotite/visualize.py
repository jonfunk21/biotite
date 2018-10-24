# This source code is part of the Biotite package and is distributed
# under the 3-Clause BSD License. Please see 'LICENSE.rst' for further
# information.

__author__ = "Patrick Kunzmann"
__all__ = ["colors", "set_font_size_in_coord", "AdaptiveFancyArrow"]

import abc
from collections import OrderedDict
import numpy as np
from numpy.linalg import norm


def set_font_size_in_coord(text, width=None, height=None, mode="unlocked"):
    from matplotlib.transforms import Bbox
    from matplotlib.text import Text
    from matplotlib.patheffects import AbstractPathEffect

    class TextScaler(AbstractPathEffect):
        def __init__(self, text, width, height, mode):
            self._text = text
            self._mode = mode
            self._width = width
            self._height = height

        def draw_path(self, renderer, gc, tpath, affine, rgbFace=None):
            ax = self._text.axes
            renderer = ax.get_figure().canvas.get_renderer()
            bbox = text.get_window_extent(renderer=renderer)
            bbox = Bbox(ax.transData.inverted().transform(bbox))
            
            if self._mode == "proportional":
                if self._width is None:
                    # Proportional scaling based on height
                    scale_y = self._height / bbox.height
                    scale_x = scale_y
                elif self._height is None:
                    # Proportional scaling based on width
                    scale_x = self._width / bbox.width
                    scale_y = scale_x
            elif self._mode == "unlocked":
                scale_x = self._width / bbox.width
                scale_y = self._height / bbox.height
            elif self._mode == "minimum":
                scale_x = self._width / bbox.width
                scale_y = self._height / bbox.height
                scale = max(scale_x, scale_y)
                scale_x, scale_y = scale, scale
            elif self._mode == "maximum":
                scale_x = self._width / bbox.width
                scale_y = self._height / bbox.height
                scale = min(scale_x, scale_y)
                scale_x, scale_y = scale, scale

            affine = affine.identity().scale(scale_x, scale_y) + affine
            renderer.draw_path(gc, tpath, affine, rgbFace)
    
    if mode in ["unlocked", "minimum", "maximum"]:
        if width is None or height is None:
            raise TypeError(
                f"Width and height must be set in '{mode}' mode"
            )
    elif mode == "proportional":
        if  not (width  is None and height is not None) or \
            not (height is None and width  is not None):
                raise TypeError(
                    f"Either width or height must be set in '{mode}' mode"
                )
    else:
        raise ValueError(
                f"Unknown mode '{mode}'"
            )
    text.set_path_effects([TextScaler(text, width, height, mode)])

try:
    # Only create this class when matplotlib is installed
    from matplotlib.transforms import Bbox
    from matplotlib.patches import FancyArrow
    from matplotlib.patheffects import AbstractPathEffect

    class AdaptiveFancyArrow(FancyArrow):

        def __init__(self, x, y, dx, dy,
                     tail_width, head_width, head_ratio, draw_head=True,
                     shape="full", **kwargs):
            import matplotlib.pyplot as plt
            self._x = x
            self._y = y
            self._dx = dx
            self._dy = dy
            self._tail_width = tail_width
            self._head_width = head_width
            self._head_ratio = head_ratio
            self._draw_head = draw_head
            self._shape = shape
            self._kwargs = kwargs
            if not draw_head:
                head_width = tail_width
            super().__init__(
                x, y, dx, dy,
                width=tail_width, head_width=head_width,
                overhang=0, shape=shape,
                length_includes_head=True, **kwargs
            )

        def draw(self, renderer):
            arrow_box = Bbox([(0,0), (0,self._head_width)])
            arrow_box_display = self.axes.transData.transform_bbox(arrow_box)
            head_length_display = np.abs(
                arrow_box_display.height * self._head_ratio
            )
            arrow_box_display.x1 = arrow_box_display.x0 + head_length_display
            # Transfrom back to data coordinates for plotting
            arrow_box = self.axes.transData.inverted().transform_bbox(
                arrow_box_display
            )
            head_length = arrow_box.width
            arrow_length = norm((self._dx, self._dy))
            if head_length > arrow_length:
                # If the head would be longer than the entire arrow,
                # only draw the arrow head with reduced length
                head_length = arrow_length
            if not self._draw_head:
                head_length = 0 

            # Renew the arrow's properties
            super().__init__(
                self._x, self._y, self._dx, self._dy,
                width=self._tail_width, head_width=self._head_width,
                overhang=0, shape=self._shape,
                head_length=head_length, length_includes_head=True,
                axes=self.axes, transform=self.get_transform(), **self._kwargs
            )
            self.set_clip_path(self.axes.patch)
            super().draw(renderer)


except ImportError:
    pass
    

# Biotite themed colors
colors = OrderedDict([
    ("brightorange" , "#ffb569ff"),
    ("lightorange"  , "#ff982dff"),
    ("orange"       , "#ff8405ff"),
    ("dimorange"    , "#dc7000ff"),
    ("darkorange"   , "#b45c00ff"),
    ("brightgreen"  , "#98e97fff"),
    ("lightgreen"   , "#6fe04cff"),
    ("green"        , "#52da2aff"),
    ("dimgreen"     , "#45bc20ff"),
    ("darkgreen"    , "#389a1aff"),
])