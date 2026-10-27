"""Custom report theme: deep navy + amber/teal ('TradeWar Navy Amber'). Written to StaticResources/RegisteredResources."""
NAVY, AMBER, TEAL, CORAL, SLATE, SKY = "#0B1F3A", "#F2A541", "#1AA39A", "#E4572E", "#5B6B82", "#3A86FF"
PAGE_BG, CARD_BORDER, INK = "#EEF2F7", "#DCE3EE", "#33415C"
FONT, FONT_B = "Segoe UI", "Segoe UI Semibold"


def s(c: str) -> dict:
    return {"solid": {"color": c}}


THEME = {
    "name": "TradeWar Navy Amber",
    "dataColors": [TEAL, AMBER, SKY, CORAL, SLATE, "#8E6CDF", "#2EC4B6", "#FFCA3A", NAVY, "#C2185B", "#7FB800", "#A0AEC0"],
    "background": "#FFFFFF", "foreground": NAVY, "tableAccent": TEAL,
    "good": TEAL, "neutral": AMBER, "bad": CORAL, "maximum": TEAL, "center": "#F4F6FA", "minimum": CORAL, "null": "#C9D2DE",
    "textClasses": {
        "callout": {"fontFace": FONT_B, "fontSize": 22, "color": NAVY},
        "title": {"fontFace": FONT_B, "fontSize": 11, "color": NAVY},
        "header": {"fontFace": FONT_B, "fontSize": 11, "color": NAVY},
        "label": {"fontFace": FONT, "fontSize": 9, "color": INK},
        "largeTitle": {"fontFace": FONT_B, "fontSize": 18, "color": NAVY},
    },
    "visualStyles": {
        "*": {"*": {
            "background": [{"show": True, "color": s("#FFFFFF"), "transparency": 0}],
            "border": [{"show": True, "color": s(CARD_BORDER), "radius": 10, "width": 1}],
            "dropShadow": [{"show": True, "color": s("#0B1F3A"), "transparency": 92, "position": "Outer", "preset": "BottomRight"}],
            "title": [{"show": True, "fontColor": s(NAVY), "fontSize": 11, "fontFamily": FONT_B, "titleWrap": True}],
            "padding": [{"top": 6, "bottom": 6, "left": 10, "right": 10}],
            "visualHeader": [{"show": True, "background": s("#FFFFFF"), "foreground": s(SLATE)}],
            "categoryAxis": [{"labelColor": s(INK), "fontSize": 9, "gridlineShow": False, "titleColor": s(SLATE)}],
            "valueAxis": [{"labelColor": s(INK), "fontSize": 9, "gridlineColor": s("#E6EBF2"), "gridlineStyle": "dotted", "titleColor": s(SLATE)}],
            "legend": [{"show": True, "position": "Top", "labelColor": s(INK), "fontSize": 9}],
        }},
        "page": {"*": {"background": [{"color": s(PAGE_BG), "transparency": 0}], "outspace": [{"color": s("#E3E9F1")}]}},
        "card": {"*": {
            "labels": [{"color": s(NAVY), "fontSize": 22, "fontFamily": FONT_B, "labelDisplayUnits": 1}],
            "categoryLabels": [{"show": True, "color": s(SLATE), "fontSize": 9, "fontFamily": FONT}],
            "title": [{"show": False}],
            "border": [{"show": True, "color": s(CARD_BORDER), "radius": 10}],
        }},
        "slicer": {"*": {
            "header": [{"show": True, "fontColor": s(SLATE), "textSize": 9, "fontFamily": FONT_B}],
            "items": [{"fontColor": s(NAVY), "textSize": 10}],
            "title": [{"show": False}],
        }},
        "textbox": {"*": {"background": [{"show": False}], "border": [{"show": False}], "dropShadow": [{"show": False}],
                          "visualHeader": [{"show": False}]}},
        "pageNavigator": {"*": {"background": [{"show": False}], "border": [{"show": False}], "dropShadow": [{"show": False}],
                                "visualHeader": [{"show": False}]}},
        "tableEx": {"*": {"grid": [{"gridHorizontal": True, "gridHorizontalColor": s("#EEF2F7"), "rowPadding": 3}],
                          "columnHeaders": [{"fontColor": s("#FFFFFF"), "backColor": s(NAVY), "fontFamily": FONT_B}],
                          "values": [{"fontColor": s(INK), "backColor": s("#FFFFFF"), "backColorSecondary": s("#F7F9FC")}]}},
        "pivotTable": {"*": {"columnHeaders": [{"fontColor": s("#FFFFFF"), "backColor": s(NAVY), "fontFamily": FONT_B}],
                             "rowHeaders": [{"fontColor": s(NAVY), "fontFamily": FONT}]}},
        "lineChart": {"*": {"lineStyles": [{"strokeWidth": 2}]}},
    },
}
