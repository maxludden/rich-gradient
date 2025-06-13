import re
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Tuple, cast

from rich.color import Color as RichColor
from rich.color_triplet import ColorTriplet
from rich.console import Console
from rich.style import Style
from rich.text import Text

from rich_gradient._parsers import (
    r_hex_long,
    r_hex_short,
    r_hsl,
    r_hsl_v4_style,
    r_rgb,
    r_rgb_v4_style,
    rads,
    repeat_colors,
)

NAMES: List[str] = [
    "magenta",
    "purple",
    "blue",
    "lightblue",
    "cyan",
    "lime",
    "green",
    "yellow",
    "orange",
    "darkorange",
    "red",
    "hotpink",
    "aliceblue",
    "antiquewhite",
    "azure",
    "beige",
    "bisque",
    "black",
    "blanchedalmond",
    "brown",
    "burlywood",
    "cadetblue",
    "chartreuse",
    "chocolate",
    "coral",
    "cornflowerblue",
    "cornsilk",
    "crimson",
    "darkblue",
    "darkcyan",
    "darkgoldenrod",
    "darkgray",
    "darkgreen",
    "darkgrey",
    "darkkhaki",
    "darkmagenta",
    "darkolivegreen",
    "darkorange_css",
    "darkorchid",
    "darkred",
    "darksalmon",
    "darkseagreen",
    "darkslateblue",
    "darkslategray",
    "darkslategrey",
    "darkturquoise",
    "darkviolet",
    "skyblue_css",
    "dimgray",
    "dimgrey",
    "dodgerblue",
    "firebrick",
    "floralwhite",
    "forestgreen",
    "gainsboro",
    "ghostwhite",
    "gold",
    "goldenrod",
    "gray",
    "green_css",
    "greenyellow",
    "grey",
    "honeydew",
    "hotpink_css",
    "indianred",
    "indigo",
    "ivory",
    "khaki",
    "lavender",
    "lavenderblush",
    "lawngreen_css",
    "lemonchiffon",
    "lightblue_css",
    "lightcoral",
    "lightcyan",
    "lightgoldenrodyellow",
    "lightgray",
    "lightgreen",
    "lightgrey",
    "lightpink",
    "lightsalmon",
    "lightseagreen",
    "lightskyblue_css",
    "lightslategray",
    "lightslategrey",
    "lightsteelblue",
    "lightyellow",
    "limegreen",
    "linen",
    "maroon",
    "mediumaquamarine",
    "mediumblue",
    "mediumorchid",
    "mediumpurple",
    "mediumseagreen",
    "mediumslateblue",
    "springgreen",
    "mediumturquoise",
    "mediumvioletred",
    "midnightblue",
    "mintcream",
    "mistyrose",
    "moccasin",
    "navajowhite",
    "navy",
    "oldlace",
    "olive",
    "olivedrab",
    "orchid",
    "palegoldenrod",
    "palegreen",
    "paleturquoise",
    "palevioletred",
    "papayawhip",
    "peachpuff",
    "peru",
    "pink",
    "plum",
    "powderblue",
    "rosybrown",
    "royalblue",
    "saddlebrown",
    "salmon",
    "sandybrown",
    "seagreen",
    "seashell",
    "sienna",
    "silver",
    "slateblue",
    "slategray",
    "slategrey",
    "snow",
    "steelblue",
    "tan",
    "teal",
    "thistle",
    "tomato",
    "aqua",
    "violet",
    "wheat",
    "white",
    "whitesmoke",
    "yellowgreen",
    "bright_black",
    "bright_red",
    "bright_green",
    "bright_yellow",
    "bright_blue",
    "bright_magenta",
    "bright_cyan",
    "bright_white",
    "grey0",
    "navy_blue",
    "dark_blue",
    "blue3",
    "dark_green",
    "deep_sky_blue4",
    "dodger_blue3",
    "green4",
    "spring_green4",
    "turquoise4",
    "deep_sky_blue3",
    "dark_cyan",
    "light_sea_green",
    "deep_sky_blue2",
    "green3",
    "spring_green3",
    "cyan3",
    "dark_turquoise",
    "turquoise2",
    "spring_green2",
    "cyan2",
    "purple4",
    "purple3",
    "grey37",
    "medium_purple4",
    "slate_blue3",
    "royal_blue1",
    "chartreuse4",
    "pale_turquoise4",
    "steel_blue",
    "steel_blue3",
    "cornflower_blue",
    "dark_sea_green4",
    "cadet_blue",
    "sky_blue3",
    "chartreuse3",
    "sea_green3",
    "aquamarine3",
    "medium_turquoise",
    "steel_blue1",
    "sea_green2",
    "sea_green1",
    "dark_slate_gray2",
    "dark_red",
    "dark_magenta",
    "orange4",
    "light_pink4",
    "plum4",
    "medium_purple3",
    "slate_blue1",
    "wheat4",
    "grey53",
    "light_slate_grey",
    "medium_purple",
    "light_slate_blue",
    "yellow4",
    "dark_sea_green",
    "light_sky_blue3",
    "sky_blue2",
    "chartreuse2",
    "pale_green3",
    "dark_slate_gray3",
    "sky_blue1",
    "light_green",
    "aquamarine1",
    "dark_slate_gray1",
    "deep_pink4",
    "medium_violet_red",
    "dark_violet",
    "medium_orchid3",
    "medium_orchid",
    "dark_goldenrod",
    "rosy_brown",
    "grey63",
    "medium_purple2",
    "medium_purple1",
    "dark_khaki",
    "navajo_white3",
    "grey69",
    "light_steel_blue3",
    "light_steel_blue",
    "dark_olive_green3",
    "dark_sea_green3",
    "light_cyan3",
    "light_sky_blue1",
    "dark_olive_green2",
    "pale_green1",
    "dark_sea_green2",
    "pale_turquoise1",
    "red3",
    "deep_pink3",
    "magenta3",
    "dark_orange3",
    "indian_red",
    "hot_pink3",
    "hot_pink2",
    "orange3",
    "light_salmon3",
    "light_pink3",
    "pink3",
    "plum3",
    "gold3",
    "light_goldenrod3",
    "misty_rose3",
    "thistle3",
    "plum2",
    "yellow3",
    "khaki3",
    "light_yellow3",
    "grey84",
    "light_steel_blue1",
    "yellow2",
    "dark_olive_green1",
    "dark_sea_green1",
    "honeydew2",
    "light_cyan1",
    "magenta2",
    "indian_red1",
    "hot_pink",
    "medium_orchid1",
    "darkorange",
    "salmon1",
    "light_coral",
    "pale_violet_red1",
    "orchid2",
    "orchid1",
    "sandy_brown",
    "light_salmon1",
    "light_pink1",
    "pink1",
    "plum1",
    "gold1",
    "light_goldenrod2",
    "navajo_white1",
    "misty_rose1",
    "thistle1",
    "light_goldenrod1",
    "khaki1",
    "wheat1",
    "cornsilk1",
    "grey100",
    "grey3",
    "grey7",
    "grey11",
    "grey15",
    "grey19",
    "grey23",
    "grey27",
    "grey30",
    "grey35",
    "grey39",
    "grey42",
    "grey46",
    "grey50",
    "grey54",
    "grey58",
    "grey62",
    "grey66",
    "grey70",
    "grey74",
    "grey78",
    "grey82",
    "grey85",
    "grey89",
    "grey93",
]
COLOR_TUPLES: List[Tuple[int, int, int]] = [
    (255, 0, 255),
    (175, 75, 255),
    (50, 105, 255),
    (0, 153, 255),
    (0, 255, 255),
    (0, 255, 0),
    (175, 255, 0),
    (255, 255, 0),
    (255, 175, 0),
    (255, 135, 0),
    (255, 0, 0),
    (255, 0, 135),
    (240, 248, 255),
    (250, 235, 215),
    (240, 255, 255),
    (245, 245, 220),
    (255, 228, 196),
    (0, 0, 0),
    (255, 235, 205),
    (165, 42, 42),
    (222, 184, 135),
    (95, 158, 160),
    (127, 255, 0),
    (210, 105, 30),
    (255, 127, 80),
    (100, 149, 237),
    (255, 248, 220),
    (220, 20, 60),
    (0, 0, 139),
    (0, 139, 139),
    (184, 134, 11),
    (169, 169, 169),
    (0, 100, 0),
    (169, 169, 169),
    (189, 183, 107),
    (139, 0, 139),
    (85, 107, 47),
    (255, 140, 0),
    (153, 50, 204),
    (139, 0, 0),
    (233, 150, 122),
    (143, 188, 143),
    (72, 61, 139),
    (47, 79, 79),
    (47, 79, 79),
    (0, 206, 209),
    (148, 0, 211),
    (0, 191, 255),
    (105, 105, 105),
    (105, 105, 105),
    (30, 144, 255),
    (178, 34, 34),
    (255, 250, 240),
    (34, 139, 34),
    (220, 220, 220),
    (248, 248, 255),
    (255, 215, 0),
    (218, 165, 32),
    (128, 128, 128),
    (0, 128, 0),
    (173, 255, 47),
    (128, 128, 128),
    (240, 255, 240),
    (255, 105, 180),
    (205, 92, 92),
    (75, 0, 130),
    (255, 255, 240),
    (240, 230, 140),
    (230, 230, 250),
    (255, 240, 245),
    (124, 252, 0),
    (255, 250, 205),
    (173, 216, 230),
    (240, 128, 128),
    (224, 255, 255),
    (250, 250, 210),
    (211, 211, 211),
    (144, 238, 144),
    (211, 211, 211),
    (255, 182, 193),
    (255, 160, 122),
    (32, 178, 170),
    (135, 206, 250),
    (119, 136, 153),
    (119, 136, 153),
    (176, 196, 222),
    (255, 255, 224),
    (50, 205, 50),
    (250, 240, 230),
    (128, 0, 0),
    (102, 205, 170),
    (0, 0, 205),
    (186, 85, 211),
    (147, 112, 219),
    (60, 179, 113),
    (123, 104, 238),
    (0, 250, 154),
    (72, 209, 204),
    (199, 21, 133),
    (25, 25, 112),
    (245, 255, 250),
    (255, 228, 225),
    (255, 228, 181),
    (255, 222, 173),
    (0, 0, 128),
    (253, 245, 230),
    (128, 128, 0),
    (107, 142, 35),
    (218, 112, 214),
    (238, 232, 170),
    (152, 251, 152),
    (175, 238, 238),
    (219, 112, 147),
    (255, 239, 213),
    (255, 218, 185),
    (205, 133, 63),
    (255, 192, 203),
    (221, 160, 221),
    (176, 224, 230),
    (188, 143, 143),
    (65, 105, 225),
    (139, 69, 19),
    (250, 128, 114),
    (244, 164, 96),
    (46, 139, 87),
    (255, 245, 238),
    (160, 82, 45),
    (192, 192, 192),
    (106, 90, 205),
    (112, 128, 144),
    (112, 128, 144),
    (255, 250, 250),
    (70, 130, 180),
    (210, 180, 140),
    (0, 128, 128),
    (216, 191, 216),
    (255, 99, 71),
    (64, 224, 208),
    (238, 130, 238),
    (245, 222, 179),
    (255, 255, 255),
    (245, 245, 245),
    (154, 205, 50),
    (45, 45, 45),
    (210, 0, 0),
    (0, 210, 0),
    (210, 210, 0),
    (0, 0, 210),
    (210, 0, 210),
    (0, 210, 210),
    (210, 210, 210),
    (0, 0, 0),
    (0, 0, 95),
    (0, 0, 135),
    (0, 0, 215),
    (0, 95, 0),
    (0, 95, 175),
    (0, 95, 215),
    (0, 135, 0),
    (0, 135, 95),
    (0, 135, 135),
    (0, 135, 215),
    (0, 175, 135),
    (0, 175, 175),
    (0, 175, 215),
    (0, 215, 0),
    (0, 215, 95),
    (0, 215, 175),
    (0, 215, 215),
    (0, 215, 255),
    (0, 255, 95),
    (0, 255, 215),
    (95, 0, 175),
    (95, 0, 215),
    (95, 95, 95),
    (95, 95, 135),
    (95, 95, 215),
    (95, 95, 255),
    (95, 135, 0),
    (95, 135, 135),
    (95, 135, 175),
    (95, 135, 215),
    (95, 135, 255),
    (95, 175, 95),
    (95, 175, 175),
    (95, 175, 215),
    (95, 215, 0),
    (95, 215, 135),
    (95, 215, 175),
    (95, 215, 215),
    (95, 215, 255),
    (95, 255, 95),
    (95, 255, 175),
    (95, 255, 255),
    (135, 0, 0),
    (135, 0, 175),
    (135, 95, 0),
    (135, 95, 95),
    (135, 95, 135),
    (135, 95, 215),
    (135, 95, 255),
    (135, 135, 95),
    (135, 135, 135),
    (135, 135, 175),
    (135, 135, 215),
    (135, 135, 255),
    (135, 175, 0),
    (135, 175, 135),
    (135, 175, 215),
    (135, 175, 255),
    (135, 215, 0),
    (135, 215, 135),
    (135, 215, 215),
    (135, 215, 255),
    (135, 255, 135),
    (135, 255, 215),
    (135, 255, 255),
    (175, 0, 95),
    (175, 0, 135),
    (175, 0, 215),
    (175, 95, 175),
    (175, 95, 215),
    (175, 135, 0),
    (175, 135, 135),
    (175, 135, 175),
    (175, 135, 215),
    (175, 135, 255),
    (175, 175, 95),
    (175, 175, 135),
    (175, 175, 175),
    (175, 175, 215),
    (175, 175, 255),
    (175, 215, 95),
    (175, 215, 135),
    (175, 215, 215),
    (175, 215, 255),
    (175, 255, 95),
    (175, 255, 135),
    (175, 255, 175),
    (175, 255, 255),
    (215, 0, 0),
    (215, 0, 135),
    (215, 0, 215),
    (215, 95, 0),
    (215, 95, 95),
    (215, 95, 135),
    (215, 95, 175),
    (215, 135, 0),
    (215, 135, 95),
    (215, 135, 135),
    (215, 135, 175),
    (215, 135, 215),
    (215, 175, 0),
    (215, 175, 95),
    (215, 175, 175),
    (215, 175, 215),
    (215, 175, 255),
    (215, 215, 0),
    (215, 215, 95),
    (215, 215, 175),
    (215, 215, 215),
    (215, 215, 255),
    (215, 255, 0),
    (215, 255, 135),
    (215, 255, 175),
    (215, 255, 215),
    (215, 255, 255),
    (255, 0, 215),
    (255, 95, 135),
    (255, 95, 215),
    (255, 95, 255),
    (255, 135, 0),
    (255, 135, 95),
    (255, 135, 135),
    (255, 135, 175),
    (255, 135, 215),
    (255, 135, 255),
    (255, 175, 95),
    (255, 175, 135),
    (255, 175, 175),
    (255, 175, 215),
    (255, 175, 255),
    (255, 215, 0),
    (255, 215, 135),
    (255, 215, 175),
    (255, 215, 215),
    (255, 215, 255),
    (255, 255, 95),
    (255, 255, 135),
    (255, 255, 175),
    (255, 255, 215),
    (255, 255, 255),
    (8, 8, 8),
    (18, 18, 18),
    (28, 28, 28),
    (38, 38, 38),
    (48, 48, 48),
    (58, 58, 58),
    (68, 68, 68),
    (78, 78, 78),
    (88, 88, 88),
    (98, 98, 98),
    (108, 108, 108),
    (118, 118, 118),
    (128, 128, 128),
    (138, 138, 138),
    (148, 148, 148),
    (158, 158, 158),
    (168, 168, 168),
    (178, 178, 178),
    (188, 188, 188),
    (198, 198, 198),
    (208, 208, 208),
    (218, 218, 218),
    (228, 228, 228),
    (238, 238, 238),
]

HEX_COLORS: List[str] = [
    "#FF00FF",
    "#AF40FF",
    "#4070FF",
    "#00AFFF",
    "#00FFFF",
    "#00FF00",
    "#AFFF00",
    "#FFFF00",
    "#FFAF00",
    "#FF8700",
    "#FF0000",
    "#FF0087",
    "#F0F8FF",
    "#FAEBD7",
    "#F0FFFF",
    "#F5F5DC",
    "#FFE4C4",
    "#000000",
    "#FFEBCD",
    "#A52A2A",
    "#DEB887",
    "#5F9EA0",
    "#7FFF00",
    "#D2691E",
    "#FF7F50",
    "#6495ED",
    "#FFF8DC",
    "#DC143C",
    "#00008B",
    "#008B8B",
    "#B8860B",
    "#A9A9A9",
    "#006400",
    "#A9A9A9",
    "#BDB76B",
    "#8B008B",
    "#556B2F",
    "#FF8C00",
    "#9932CC",
    "#8B0000",
    "#E9967A",
    "#8FBC8F",
    "#483D8B",
    "#2F4F4F",
    "#2F4F4F",
    "#00CED1",
    "#9400D3",
    "#00BFFF",
    "#696969",
    "#696969",
    "#1E90FF",
    "#B22222",
    "#FFFAF0",
    "#228B22",
    "#DCDCDC",
    "#F8F8FF",
    "#FFD700",
    "#DAA520",
    "#808080",
    "#008000",
    "#ADFF2F",
    "#808080",
    "#F0FFF0",
    "#FF69B4",
    "#CD5C5C",
    "#4B0082",
    "#FFFFF0",
    "#F0E68C",
    "#E6E6FA",
    "#FFF0F5",
    "#7CFC00",
    "#FFFACD",
    "#ADD8E6",
    "#F08080",
    "#E0FFFF",
    "#FAFAD2",
    "#D3D3D3",
    "#90EE90",
    "#D3D3D3",
    "#FFB6C1",
    "#FFA07A",
    "#20B2AA",
    "#87CEFA",
    "#778899",
    "#778899",
    "#B0C4DE",
    "#FFFFE0",
    "#32CD32",
    "#FAF0E6",
    "#800000",
    "#66CDAA",
    "#0000CD",
    "#BA55D3",
    "#9370DB",
    "#3CB371",
    "#7B68EE",
    "#00FA9A",
    "#48D1CC",
    "#C71585",
    "#191970",
    "#F5FFFA",
    "#FFE4E1",
    "#FFE4B5",
    "#FFDEAD",
    "#000080",
    "#FDF5E6",
    "#808000",
    "#6B8E23",
    "#DA70D6",
    "#EEE8AA",
    "#98FB98",
    "#AFEEEE",
    "#DB7093",
    "#FFEFD5",
    "#FFDAB9",
    "#CD853F",
    "#FFC0CB",
    "#DDA0DD",
    "#B0E0E6",
    "#BC8F8F",
    "#4169E1",
    "#8B4513",
    "#FA8072",
    "#F4A460",
    "#2E8B57",
    "#FFF5EE",
    "#A0522D",
    "#C0C0C0",
    "#6A5ACD",
    "#708090",
    "#708090",
    "#FFFAFA",
    "#4682B4",
    "#D2B48C",
    "#008080",
    "#D8BFD8",
    "#FF6347",
    "#40E0D0",
    "#EE82EE",
    "#F5DEB3",
    "#FFFFFF",
    "#F5F5F5",
    "#9ACD32",
    "#2D2D2D",
    "#D20000",
    "#00D200",
    "#D2D200",
    "#0000D2",
    "#D200D2",
    "#00D2D2",
    "#D2D2D2",
    "#000000",
    "#00005F",
    "#000087",
    "#0000D7",
    "#005F00",
    "#005FAF",
    "#005FD7",
    "#008700",
    "#00875F",
    "#008787",
    "#0087D7",
    "#00AF87",
    "#00AFAF",
    "#00AFD7",
    "#00D700",
    "#00D75F",
    "#00D7AF",
    "#00D7D7",
    "#00D7FF",
    "#00FF5F",
    "#00FFD7",
    "#5F00AF",
    "#5F00D7",
    "#5F5F5F",
    "#5F5F87",
    "#5F5FD7",
    "#5F5FFF",
    "#5F8700",
    "#5F8787",
    "#5F87AF",
    "#5F87D7",
    "#5F87FF",
    "#5FAF5F",
    "#5FAFAF",
    "#5FAFD7",
    "#5FD700",
    "#5FD787",
    "#5FD7AF",
    "#5FD7D7",
    "#5FD7FF",
    "#5FFF5F",
    "#5FFFAF",
    "#5FFFFF",
    "#870000",
    "#8700AF",
    "#875F00",
    "#875F5F",
    "#875F87",
    "#875FD7",
    "#875FFF",
    "#87875F",
    "#878787",
    "#8787AF",
    "#8787D7",
    "#8787FF",
    "#87AF00",
    "#87AF87",
    "#87AFD7",
    "#87AFFF",
    "#87D700",
    "#87D787",
    "#87D7D7",
    "#87D7FF",
    "#87FF87",
    "#87FFD7",
    "#87FFFF",
    "#AF005F",
    "#AF0087",
    "#AF00D7",
    "#AF5FAF",
    "#AF5FD7",
    "#AF8700",
    "#AF8787",
    "#AF87AF",
    "#AF87D7",
    "#AF87FF",
    "#AFAF5F",
    "#AFAF87",
    "#AFAFAF",
    "#AFAFD7",
    "#AFAFFF",
    "#AFD75F",
    "#AFD787",
    "#AFD7D7",
    "#AFD7FF",
    "#AFFF5F",
    "#AFFF87",
    "#AFFFAF",
    "#AFFFFF",
    "#D70000",
    "#D70087",
    "#D700D7",
    "#D75F00",
    "#D75F5F",
    "#D75F87",
    "#D75FAF",
    "#D78700",
    "#D7875F",
    "#D78787",
    "#D787AF",
    "#D787D7",
    "#D7AF00",
    "#D7AF5F",
    "#D7AFAF",
    "#D7AFD7",
    "#D7AFFF",
    "#D7D700",
    "#D7D75F",
    "#D7D7AF",
    "#D7D7D7",
    "#D7D7FF",
    "#D7FF00",
    "#D7FF87",
    "#D7FFAF",
    "#D7FFD7",
    "#D7FFFF",
    "#FF00D7",
    "#FF5F87",
    "#FF5FD7",
    "#FF5FFF",
    "#FF8700",
    "#FF875F",
    "#FF8787",
    "#FF87AF",
    "#FF87D7",
    "#FF87FF",
    "#FFAF5F",
    "#FFAF87",
    "#FFAFAF",
    "#FFAFD7",
    "#FFAFFF",
    "#FFD700",
    "#FFD787",
    "#FFD7AF",
    "#FFD7D7",
    "#FFD7FF",
    "#FFFF5F",
    "#FFFF87",
    "#FFFFAF",
    "#FFFFD7",
    "#FFFFFF",
    "#080808",
    "#121212",
    "#1C1C1C",
    "#262626",
    "#303030",
    "#3A3A3A",
    "#444444",
    "#4E4E4E",
    "#585858",
    "#626262",
    "#6C6C6C",
    "#767676",
    "#808080",
    "#8A8A8A",
    "#949494",
    "#9E9E9E",
    "#A8A8A8",
    "#B2B2B2",
    "#BCBCBC",
    "#C6C6C6",
    "#D0D0D0",
    "#DADADA",
    "#E4E4E4",
    "#EEEEEE",
]

RGB_COLORS: List = [
    "rgb(255, 0, 255)"
    "rgb(175, 75, 255)"
    "rgb(50, 105, 255)"
    "rgb(0, 153, 255)"
    "rgb(0, 255, 255)"
    "rgb(0, 255, 0)"
    "rgb(175, 255, 0)"
    "rgb(255, 255, 0)"
    "rgb(255, 175, 0)"
    "rgb(255, 135, 0)"
    "rgb(255, 0, 0)"
    "rgb(255, 0, 135)"
    "rgb(240, 248, 255)"
    "rgb(250, 235, 215)"
    "rgb(240, 255, 255)"
    "rgb(245, 245, 220)"
    "rgb(255, 228, 196)"
    "rgb(0, 0, 0)"
    "rgb(255, 235, 205)"
    "rgb(165, 42, 42)"
    "rgb(222, 184, 135)"
    "rgb(95, 158, 160)"
    "rgb(127, 255, 0)"
    "rgb(210, 105, 30)"
    "rgb(255, 127, 80)"
    "rgb(100, 149, 237)"
    "rgb(255, 248, 220)"
    "rgb(220, 20, 60)"
    "rgb(0, 0, 139)"
    "rgb(0, 139, 139)"
    "rgb(184, 134, 11)"
    "rgb(169, 169, 169)"
    "rgb(0, 100, 0)"
    "rgb(169, 169, 169)"
    "rgb(189, 183, 107)"
    "rgb(139, 0, 139)"
    "rgb(85, 107, 47)"
    "rgb(255, 140, 0)"
    "rgb(153, 50, 204)"
    "rgb(139, 0, 0)"
    "rgb(233, 150, 122)"
    "rgb(143, 188, 143)"
    "rgb(72, 61, 139)"
    "rgb(47, 79, 79)"
    "rgb(47, 79, 79)"
    "rgb(0, 206, 209)"
    "rgb(148, 0, 211)"
    "rgb(0, 191, 255)"
    "rgb(105, 105, 105)"
    "rgb(105, 105, 105)"
    "rgb(30, 144, 255)"
    "rgb(178, 34, 34)"
    "rgb(255, 250, 240)"
    "rgb(34, 139, 34)"
    "rgb(220, 220, 220)"
    "rgb(248, 248, 255)"
    "rgb(255, 215, 0)"
    "rgb(218, 165, 32)"
    "rgb(128, 128, 128)"
    "rgb(0, 128, 0)"
    "rgb(173, 255, 47)"
    "rgb(128, 128, 128)"
    "rgb(240, 255, 240)"
    "rgb(255, 105, 180)"
    "rgb(205, 92, 92)"
    "rgb(75, 0, 130)"
    "rgb(255, 255, 240)"
    "rgb(240, 230, 140)"
    "rgb(230, 230, 250)"
    "rgb(255, 240, 245)"
    "rgb(124, 252, 0)"
    "rgb(255, 250, 205)"
    "rgb(173, 216, 230)"
    "rgb(240, 128, 128)"
    "rgb(224, 255, 255)"
    "rgb(250, 250, 210)"
    "rgb(211, 211, 211)"
    "rgb(144, 238, 144)"
    "rgb(211, 211, 211)"
    "rgb(255, 182, 193)"
    "rgb(255, 160, 122)"
    "rgb(32, 178, 170)"
    "rgb(135, 206, 250)"
    "rgb(119, 136, 153)"
    "rgb(119, 136, 153)"
    "rgb(176, 196, 222)"
    "rgb(255, 255, 224)"
    "rgb(50, 205, 50)"
    "rgb(250, 240, 230)"
    "rgb(128, 0, 0)"
    "rgb(102, 205, 170)"
    "rgb(0, 0, 205)"
    "rgb(186, 85, 211)"
    "rgb(147, 112, 219)"
    "rgb(60, 179, 113)"
    "rgb(123, 104, 238)"
    "rgb(0, 250, 154)"
    "rgb(72, 209, 204)"
    "rgb(199, 21, 133)"
    "rgb(25, 25, 112)"
    "rgb(245, 255, 250)"
    "rgb(255, 228, 225)"
    "rgb(255, 228, 181)"
    "rgb(255, 222, 173)"
    "rgb(0, 0, 128)"
    "rgb(253, 245, 230)"
    "rgb(128, 128, 0)"
    "rgb(107, 142, 35)"
    "rgb(218, 112, 214)"
    "rgb(238, 232, 170)"
    "rgb(152, 251, 152)"
    "rgb(175, 238, 238)"
    "rgb(219, 112, 147)"
    "rgb(255, 239, 213)"
    "rgb(255, 218, 185)"
    "rgb(205, 133, 63)"
    "rgb(255, 192, 203)"
    "rgb(221, 160, 221)"
    "rgb(176, 224, 230)"
    "rgb(188, 143, 143)"
    "rgb(65, 105, 225)"
    "rgb(139, 69, 19)"
    "rgb(250, 128, 114)"
    "rgb(244, 164, 96)"
    "rgb(46, 139, 87)"
    "rgb(255, 245, 238)"
    "rgb(160, 82, 45)"
    "rgb(192, 192, 192)"
    "rgb(106, 90, 205)"
    "rgb(112, 128, 144)"
    "rgb(112, 128, 144)"
    "rgb(255, 250, 250)"
    "rgb(70, 130, 180)"
    "rgb(210, 180, 140)"
    "rgb(0, 128, 128)"
    "rgb(216, 191, 216)"
    "rgb(255, 99, 71)"
    "rgb(64, 224, 208)"
    "rgb(238, 130, 238)"
    "rgb(245, 222, 179)"
    "rgb(255, 255, 255)"
    "rgb(245, 245, 245)"
    "rgb(154, 205, 50)"
    "rgb(45, 45, 45)"
    "rgb(210, 0, 0)"
    "rgb(0, 210, 0)"
    "rgb(210, 210, 0)"
    "rgb(0, 0, 210)"
    "rgb(210, 0, 210)"
    "rgb(0, 210, 210)"
    "rgb(210, 210, 210)"
    "rgb(0, 0, 0)"
    "rgb(0, 0, 95)"
    "rgb(0, 0, 135)"
    "rgb(0, 0, 215)"
    "rgb(0, 95, 0)"
    "rgb(0, 95, 175)"
    "rgb(0, 95, 215)"
    "rgb(0, 135, 0)"
    "rgb(0, 135, 95)"
    "rgb(0, 135, 135)"
    "rgb(0, 135, 215)"
    "rgb(0, 175, 135)"
    "rgb(0, 175, 175)"
    "rgb(0, 175, 215)"
    "rgb(0, 215, 0)"
    "rgb(0, 215, 95)"
    "rgb(0, 215, 175)"
    "rgb(0, 215, 215)"
    "rgb(0, 215, 255)"
    "rgb(0, 255, 95)"
    "rgb(0, 255, 215)"
    "rgb(95, 0, 175)"
    "rgb(95, 0, 215)"
    "rgb(95, 95, 95)"
    "rgb(95, 95, 135)"
    "rgb(95, 95, 215)"
    "rgb(95, 95, 255)"
    "rgb(95, 135, 0)"
    "rgb(95, 135, 135)"
    "rgb(95, 135, 175)"
    "rgb(95, 135, 215)"
    "rgb(95, 135, 255)"
    "rgb(95, 175, 95)"
    "rgb(95, 175, 175)"
    "rgb(95, 175, 215)"
    "rgb(95, 215, 0)"
    "rgb(95, 215, 135)"
    "rgb(95, 215, 175)"
    "rgb(95, 215, 215)"
    "rgb(95, 215, 255)"
    "rgb(95, 255, 95)"
    "rgb(95, 255, 175)"
    "rgb(95, 255, 255)"
    "rgb(135, 0, 0)"
    "rgb(135, 0, 175)"
    "rgb(135, 95, 0)"
    "rgb(135, 95, 95)"
    "rgb(135, 95, 135)"
    "rgb(135, 95, 215)"
    "rgb(135, 95, 255)"
    "rgb(135, 135, 95)"
    "rgb(135, 135, 135)"
    "rgb(135, 135, 175)"
    "rgb(135, 135, 215)"
    "rgb(135, 135, 255)"
    "rgb(135, 175, 0)"
    "rgb(135, 175, 135)"
    "rgb(135, 175, 215)"
    "rgb(135, 175, 255)"
    "rgb(135, 215, 0)"
    "rgb(135, 215, 135)"
    "rgb(135, 215, 215)"
    "rgb(135, 215, 255)"
    "rgb(135, 255, 135)"
    "rgb(135, 255, 215)"
    "rgb(135, 255, 255)"
    "rgb(175, 0, 95)"
    "rgb(175, 0, 135)"
    "rgb(175, 0, 215)"
    "rgb(175, 95, 175)"
    "rgb(175, 95, 215)"
    "rgb(175, 135, 0)"
    "rgb(175, 135, 135)"
    "rgb(175, 135, 175)"
    "rgb(175, 135, 215)"
    "rgb(175, 135, 255)"
    "rgb(175, 175, 95)"
    "rgb(175, 175, 135)"
    "rgb(175, 175, 175)"
    "rgb(175, 175, 215)"
    "rgb(175, 175, 255)"
    "rgb(175, 215, 95)"
    "rgb(175, 215, 135)"
    "rgb(175, 215, 215)"
    "rgb(175, 215, 255)"
    "rgb(175, 255, 95)"
    "rgb(175, 255, 135)"
    "rgb(175, 255, 175)"
    "rgb(175, 255, 255)"
    "rgb(215, 0, 0)"
    "rgb(215, 0, 135)"
    "rgb(215, 0, 215)"
    "rgb(215, 95, 0)"
    "rgb(215, 95, 95)"
    "rgb(215, 95, 135)"
    "rgb(215, 95, 175)"
    "rgb(215, 135, 0)"
    "rgb(215, 135, 95)"
    "rgb(215, 135, 135)"
    "rgb(215, 135, 175)"
    "rgb(215, 135, 215)"
    "rgb(215, 175, 0)"
    "rgb(215, 175, 95)"
    "rgb(215, 175, 175)"
    "rgb(215, 175, 215)"
    "rgb(215, 175, 255)"
    "rgb(215, 215, 0)"
    "rgb(215, 215, 95)"
    "rgb(215, 215, 175)"
    "rgb(215, 215, 215)"
    "rgb(215, 215, 255)"
    "rgb(215, 255, 0)"
    "rgb(215, 255, 135)"
    "rgb(215, 255, 175)"
    "rgb(215, 255, 215)"
    "rgb(215, 255, 255)"
    "rgb(255, 0, 215)"
    "rgb(255, 95, 135)"
    "rgb(255, 95, 215)"
    "rgb(255, 95, 255)"
    "rgb(255, 135, 0)"
    "rgb(255, 135, 95)"
    "rgb(255, 135, 135)"
    "rgb(255, 135, 175)"
    "rgb(255, 135, 215)"
    "rgb(255, 135, 255)"
    "rgb(255, 175, 95)"
    "rgb(255, 175, 135)"
    "rgb(255, 175, 175)"
    "rgb(255, 175, 215)"
    "rgb(255, 175, 255)"
    "rgb(255, 215, 0)"
    "rgb(255, 215, 135)"
    "rgb(255, 215, 175)"
    "rgb(255, 215, 215)"
    "rgb(255, 215, 255)"
    "rgb(255, 255, 95)"
    "rgb(255, 255, 135)"
    "rgb(255, 255, 175)"
    "rgb(255, 255, 215)"
    "rgb(255, 255, 255)"
    "rgb(8, 8, 8)"
    "rgb(18, 18, 18)"
    "rgb(28, 28, 28)"
    "rgb(38, 38, 38)"
    "rgb(48, 48, 48)"
    "rgb(58, 58, 58)"
    "rgb(68, 68, 68)"
    "rgb(78, 78, 78)"
    "rgb(88, 88, 88)"
    "rgb(98, 98, 98)"
    "rgb(108, 108, 108)"
    "rgb(118, 118, 118)"
    "rgb(128, 128, 128)"
    "rgb(138, 138, 138)"
    "rgb(148, 148, 148)"
    "rgb(158, 158, 158)"
    "rgb(168, 168, 168)"
    "rgb(178, 178, 178)"
    "rgb(188, 188, 188)"
    "rgb(198, 198, 198)"
    "rgb(208, 208, 208)"
    "rgb(218, 218, 218)"
    "rgb(228, 228, 228)"
    "rgb(238, 238, 238)"
]

ANSI_COLORS: List[int] = [
    5,
    129,
    177,
    4,
    -1,
    -1,
    -1,
    6,
    -1,
    -1,
    -1,
    3,
    -1,
    -1,
    -1,
    1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    0,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    2,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    170,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    180,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    7,
    -1,
    -1,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    20,
    22,
    25,
    26,
    28,
    29,
    30,
    32,
    36,
    37,
    38,
    40,
    41,
    43,
    44,
    45,
    47,
    50,
    55,
    56,
    59,
    60,
    62,
    63,
    64,
    66,
    67,
    68,
    69,
    71,
    73,
    74,
    76,
    78,
    79,
    80,
    81,
    83,
    85,
    87,
    88,
    91,
    94,
    95,
    96,
    98,
    99,
    101,
    102,
    103,
    104,
    105,
    106,
    108,
    110,
    111,
    112,
    114,
    116,
    117,
    120,
    122,
    123,
    125,
    126,
    128,
    133,
    134,
    136,
    138,
    139,
    140,
    141,
    143,
    144,
    145,
    146,
    147,
    149,
    150,
    152,
    153,
    155,
    156,
    157,
    159,
    160,
    162,
    164,
    166,
    167,
    168,
    169,
    172,
    173,
    174,
    175,
    176,
    178,
    179,
    181,
    182,
    183,
    184,
    185,
    187,
    188,
    189,
    190,
    192,
    193,
    194,
    195,
    200,
    204,
    206,
    207,
    208,
    209,
    210,
    211,
    212,
    213,
    215,
    216,
    217,
    218,
    219,
    220,
    222,
    223,
    224,
    225,
    227,
    228,
    229,
    230,
    231,
    232,
    233,
    234,
    235,
    236,
    237,
    238,
    239,
    240,
    241,
    242,
    243,
    244,
    245,
    246,
    247,
    248,
    249,
    250,
    251,
    252,
    253,
    254,
    255,
]


def create_color_mapping(key: str, start: int = 0, end: Optional[int] = None) -> Dict:
    """Create a mapping of colors based on the specified key.
    Args:
        key (str): The key to map colors by (name, tuple, rgb, hex, ansi).
        start (int, optional): The starting index for the mapping. Defaults to 0.
        end (int, optional): The ending index for the mapping. Defaults to None.
    Raises:
        ValueError: If the key is not valid.
    Returns:
        Dict: A dictionary mapping colors by the specified key to their corresponding values.
    """
    lists = {
        "name": NAMES,
        "tuple": COLOR_TUPLES,
        "rgb": RGB_COLORS,
        "hex": HEX_COLORS,
        "ansi": ANSI_COLORS,
    }
    key_lower = key.lower()
    if key_lower not in lists:
        raise ValueError(f"Invalid key: {key}. Choose one of {list(lists.keys())}")
    key_list = lists[key_lower]
    if end is None:
        end = len(NAMES)
    result = {}
    for i, item in enumerate(key_list):
        if not (start <= i < end):
            # Skip indices outside the specified range
            continue
        # Ensure every other list has an element at index i
        if any(i >= len(other_list) for k2, other_list in lists.items() if k2 != key_lower):
            continue
        value = {
            k2: other_list[i]
            for k2, other_list in lists.items()
            if k2 != key_lower
        }
        result[item] = value
    return result


COLORS_BY_NAME: Dict[str, Dict[str, Tuple[int, int, int] | str | int]] = (
    create_color_mapping("name")
)
COLORS_BY_TUPLE: Dict[Tuple[int, int, int], Dict[str, str | int]] = (
    create_color_mapping("tuple")
)
COLORS_BY_RGB: Dict[Tuple[int, int, int], Dict[str, str | int]] = (
    create_color_mapping("rgb")
)
COLORS_BY_HEX: Dict[str, Dict[str, str | Tuple[int, int, int] | int]] = (
    create_color_mapping("hex")
)
COLORS_BY_ANSI: Dict[int, Dict[str, Tuple[int, int, int] | str]] = (
    create_color_mapping("ansi")
)


if __name__ == "__main__":
    from typing import List

    from rich.console import Console
    from rich.table import Table

    console = Console()

    console.line(2)
    console.rule("[bold #0099ff]Colors by Name[/bold #0099ff]")
    console.print(COLORS_BY_NAME)
    console.line(2)
    console.rule("[bold #0099ff]Colors by Tuple[/bold #0099ff]")
    console.print(COLORS_BY_TUPLE)
    console.line(2)
    console.rule("[bold #0099ff]Colors by RGB[/bold #0099ff]")
    console.print(COLORS_BY_RGB)
    console.line(2)
    console.rule("[bold #0099ff]Colors by HEX[/bold #0099ff]")
    console.print(COLORS_BY_HEX)
    console.line(2)
    console.rule("[bold #0099ff]Colors by ANSI[/bold #0099ff]")
    console.print(COLORS_BY_ANSI)
    console.line(2)
