from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE = Path(r"D:\Codes\super-ruc")
OUT = BASE / "tmp" / "docs" / "diagrams" / "class-diagram.png"

W, H = 2200, 3200
BG = "white"
LINE = "#000000"
TEXT = "#000000"
HEADER = "#F0F0F0"
BOX = "#FFFFFF"


def get_font(size: int, bold: bool = False):
    candidates = []
    if bold:
        candidates = [
            r"C:\Windows\Fonts\timesbd.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\calibrib.ttf",
        ]
    else:
        candidates = [
            r"C:\Windows\Fonts\times.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
        ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


FONT_TITLE = get_font(24, bold=True)
FONT_BODY = get_font(18)
FONT_LABEL = get_font(16)
FONT_MULT = get_font(14)


class Box:
    def __init__(self, x, y, w, title, fields):
        self.x = x
        self.y = y
        self.w = w
        self.title = title
        self.fields = fields
        self.header_h = 46
        self.line_h = 26
        self.h = self.header_h + len(fields) * self.line_h + 18

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.w

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.h

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2


BOXES = {
    "KnowledgeSource": Box(70, 70, 300, "KnowledgeSource", ["+bigserial source_id", "+varchar source_name", "+boolean is_official", "+varchar version_label", "+date effective_date"]),
    "KnowledgeEntry": Box(70, 390, 300, "KnowledgeEntry", ["+bigserial knowledge_id", "+varchar title", "+varchar status", "+boolean ambiguity_flag", "+timestamp updated_at"]),
    "TemplateAsset": Box(70, 760, 300, "TemplateAsset", ["+bigserial template_id", "+varchar template_name", "+varchar template_type", "+varchar version_label"]),
    "PartyWorkflowNode": Box(470, 70, 300, "PartyWorkflowNode", ["+bigserial node_id", "+varchar node_code", "+varchar node_name", "+integer sequence_no", "+text due_rule_text"]),
    "PartyMemberStatus": Box(470, 390, 300, "PartyMemberStatus", ["+bigserial status_id", "+bigint student_id", "+varchar current_stage_code", "+varchar organization_type", "+timestamp next_due_at"]),
    "PartyWorkflowEvent": Box(470, 810, 300, "PartyWorkflowEvent", ["+bigserial event_id", "+bigint student_id", "+bigint node_id", "+varchar event_status", "+timestamp occurred_at"]),
    "StudentProfile": Box(870, 70, 320, "StudentProfile", ["+bigserial student_id", "+varchar student_no", "+varchar full_name", "+varchar grade_code", "+varchar class_code", "+varchar political_status"]),
    "CommonRequest": Box(870, 410, 320, "CommonRequest", ["+bigserial request_id", "+varchar request_no", "+varchar request_type", "+bigint student_id", "+varchar current_status", "+boolean formal_boundary_flag"]),
    "CommonRequestAttachment": Box(870, 830, 320, "CommonRequestAttachment", ["+bigserial attachment_id", "+bigint request_id", "+varchar file_name", "+boolean confidential_flag"]),
    "ApprovalTask": Box(870, 1130, 320, "ApprovalTask", ["+bigserial task_id", "+bigint request_id", "+varchar approver_role", "+varchar task_status", "+timestamp due_at"]),
    "ApprovalAction": Box(870, 1430, 320, "ApprovalAction", ["+bigserial action_id", "+bigint task_id", "+varchar action_type", "+timestamp action_at"]),
    "NoticeMessage": Box(1310, 70, 300, "NoticeMessage", ["+bigserial notice_id", "+varchar title", "+timestamp published_at", "+timestamp expires_at"]),
    "NoticeTargetRule": Box(1310, 390, 300, "NoticeTargetRule", ["+bigserial rule_id", "+bigint notice_id", "+varchar grade_code", "+varchar major_code", "+varchar role_code", "+boolean graduation_flag"]),
    "NoticeDelivery": Box(1310, 760, 300, "NoticeDelivery", ["+bigserial delivery_id", "+bigint notice_id", "+bigint student_id", "+varchar delivery_status", "+timestamp read_at"]),
    "ImportBatch": Box(1310, 1130, 300, "ImportBatch", ["+bigserial batch_id", "+varchar batch_no", "+varchar batch_type", "+varchar batch_status", "+varchar template_version"]),
    "DocumentAuditLog": Box(1310, 1530, 300, "DocumentAuditLog", ["+bigserial audit_id", "+varchar event_type", "+varchar entity_code", "+bigint entity_id", "+varchar result_code", "+timestamp occurred_at"]),
    "ImportBatchRow": Box(1710, 1130, 300, "ImportBatchRow", ["+bigserial row_id", "+bigint batch_id", "+integer row_no", "+text raw_payload", "+varchar validation_level", "+boolean resolved_flag"]),
    "CurriculumRuleSet": Box(1710, 70, 300, "CurriculumRuleSet", ["+bigserial rule_set_id", "+varchar grade_code", "+varchar major_code", "+varchar version_label"]),
    "CurriculumModuleRule": Box(1710, 390, 300, "CurriculumModuleRule", ["+bigserial module_rule_id", "+bigint rule_set_id", "+varchar module_code", "+varchar module_name", "+numeric required_credit"]),
    "AcademicGapResult": Box(1710, 760, 300, "AcademicGapResult", ["+bigserial gap_result_id", "+bigint student_id", "+bigint rule_set_id", "+varchar result_status", "+boolean manual_review_required"]),
}


def draw_box(draw: ImageDraw.ImageDraw, box: Box):
    draw.rounded_rectangle((box.left, box.top, box.right, box.bottom), radius=8, fill=BOX, outline=LINE, width=2)
    draw.rectangle((box.left, box.top, box.right, box.top + box.header_h), fill=HEADER, outline=LINE, width=2)
    title_bbox = draw.textbbox((0, 0), box.title, font=FONT_TITLE)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text((box.cx - title_w / 2, box.top + 10), box.title, font=FONT_TITLE, fill=TEXT)
    y = box.top + box.header_h + 8
    for field in box.fields:
        draw.text((box.left + 12, y), field, font=FONT_BODY, fill=TEXT)
        y += box.line_h


def anchor(box_name, side):
    box = BOXES[box_name]
    if side == "top":
        return (box.cx, box.top)
    if side == "bottom":
        return (box.cx, box.bottom)
    if side == "left":
        return (box.left, box.cy)
    if side == "right":
        return (box.right, box.cy)
    raise ValueError(side)


def draw_diamond(draw, point, direction, filled=False):
    x, y = point
    size = 10
    if direction == "right":
        pts = [(x, y), (x + size, y - 6), (x + 2 * size, y), (x + size, y + 6)]
    elif direction == "left":
        pts = [(x, y), (x - size, y - 6), (x - 2 * size, y), (x - size, y + 6)]
    elif direction == "down":
        pts = [(x, y), (x - 6, y + size), (x, y + 2 * size), (x + 6, y + size)]
    else:
        pts = [(x, y), (x - 6, y - size), (x, y - 2 * size), (x + 6, y - size)]
    draw.polygon(pts, outline=LINE, fill=LINE if filled else BG)


def draw_arrow(draw, point, direction):
    x, y = point
    if direction == "right":
        pts = [(x, y), (x - 10, y - 5), (x - 10, y + 5)]
    elif direction == "left":
        pts = [(x, y), (x + 10, y - 5), (x + 10, y + 5)]
    elif direction == "down":
        pts = [(x, y), (x - 5, y - 10), (x + 5, y - 10)]
    else:
        pts = [(x, y), (x - 5, y + 10), (x + 5, y + 10)]
    draw.polygon(pts, fill=LINE)


def draw_label(draw, x, y, text, font):
    bbox = draw.textbbox((x, y), text, font=font)
    pad_x = 6
    pad_y = 3
    draw.rectangle((bbox[0] - pad_x, bbox[1] - pad_y, bbox[2] + pad_x, bbox[3] + pad_y), fill=BG)
    draw.text((x, y), text, font=font, fill=TEXT)


def draw_connector(draw, points, label="", relation="association", mult_start="", mult_end="", label_offset=(0, 0)):
    draw.line(points, fill=LINE, width=3)
    start = points[0]
    second = points[1]
    end = points[-1]
    before_end = points[-2]

    if relation == "aggregation":
        direction = "right" if second[0] > start[0] else "left" if second[0] < start[0] else "down" if second[1] > start[1] else "up"
        draw_diamond(draw, start, direction, filled=False)
    elif relation == "composition":
        direction = "right" if second[0] > start[0] else "left" if second[0] < start[0] else "down" if second[1] > start[1] else "up"
        draw_diamond(draw, start, direction, filled=True)

    if relation == "association":
        direction = "right" if end[0] > before_end[0] else "left" if end[0] < before_end[0] else "down" if end[1] > before_end[1] else "up"
        draw_arrow(draw, end, direction)

    if mult_start:
        draw_label(draw, start[0] + 6, start[1] - 20, mult_start, FONT_MULT)
    if mult_end:
        draw_label(draw, end[0] - 28, end[1] - 20, mult_end, FONT_MULT)
    if label:
        mx = (points[1][0] + points[-2][0]) / 2 + label_offset[0]
        my = (points[1][1] + points[-2][1]) / 2 + label_offset[1]
        draw_label(draw, mx, my, label, FONT_LABEL)


def main():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    for box in BOXES.values():
        draw_box(draw, box)

    # Knowledge loop
    draw_connector(draw, [anchor("KnowledgeSource", "bottom"), (220, 300), anchor("KnowledgeEntry", "top")], "authoritative_for", "association", "1", "0..*", (10, -8))
    draw_connector(draw, [anchor("KnowledgeEntry", "bottom"), (220, 650), anchor("TemplateAsset", "top")], "references", "aggregation", "0..*", "0..*", (16, -8))

    # Workflow loop
    draw_connector(draw, [anchor("StudentProfile", "left"), (820, 210), (820, 470), anchor("PartyMemberStatus", "right")], "current_status", "association", "1", "0..1", (-40, -12))
    draw_connector(draw, [anchor("PartyWorkflowNode", "bottom"), (620, 740), anchor("PartyWorkflowEvent", "top")], "defines", "composition", "1", "0..*", (8, -8))
    draw_connector(draw, [anchor("PartyMemberStatus", "bottom"), (620, 760), anchor("PartyWorkflowEvent", "top")], "timeline", "association", "1", "0..*", (-46, -30))

    # Approval loop
    draw_connector(draw, [anchor("StudentProfile", "bottom"), (1030, 390), anchor("CommonRequest", "top")], "submits", "association", "1", "0..*", (8, -8))
    draw_connector(draw, [anchor("CommonRequest", "bottom"), (1030, 810), anchor("CommonRequestAttachment", "top")], "contains", "composition", "1", "0..*", (-70, -8))
    draw_connector(draw, [anchor("CommonRequest", "bottom"), (1110, 1080), anchor("ApprovalTask", "top")], "creates", "composition", "1", "0..*", (12, -8))
    draw_connector(draw, [anchor("ApprovalTask", "bottom"), (1030, 1380), anchor("ApprovalAction", "top")], "records", "composition", "1", "0..*", (10, -8))

    # Notification loop
    draw_connector(draw, [anchor("NoticeMessage", "bottom"), (1460, 340), anchor("NoticeTargetRule", "top")], "scopes", "aggregation", "1", "0..*", (-36, -8))
    draw_connector(draw, [anchor("NoticeMessage", "bottom"), (1540, 710), anchor("NoticeDelivery", "top")], "delivers", "aggregation", "1", "0..*", (16, -8))
    draw_connector(draw, [anchor("StudentProfile", "right"), (1260, 210), (1260, 840), anchor("NoticeDelivery", "left")], "receives", "association", "1", "0..*", (-10, -12))

    # Audit / file exchange loop
    draw_connector(draw, [anchor("ImportBatch", "bottom"), (1460, 1460), anchor("DocumentAuditLog", "top")], "audited_by", "association", "1", "0..*", (-80, -8))
    draw_connector(draw, [anchor("ImportBatch", "right"), (1680, 1210), anchor("ImportBatchRow", "left")], "stages", "composition", "1", "0..*", (10, -24))
    draw_connector(draw, [anchor("CommonRequest", "right"), (1260, 510), (1260, 1610), anchor("DocumentAuditLog", "left")], "audited_by", "association", "1", "0..*", (-18, -8))
    draw_connector(draw, [anchor("ApprovalAction", "right"), (1260, 1500), (1260, 1650), anchor("DocumentAuditLog", "left")], "audited_by", "association", "1", "0..*", (-8, 0))

    # Academic loop
    draw_connector(draw, [anchor("CurriculumRuleSet", "bottom"), (1860, 340), anchor("CurriculumModuleRule", "top")], "contains", "composition", "1", "0..*", (10, -8))
    draw_connector(draw, [anchor("CurriculumRuleSet", "bottom"), (1940, 720), anchor("AcademicGapResult", "top")], "evaluates", "association", "1", "0..*", (10, -8))
    draw_connector(draw, [anchor("StudentProfile", "right"), (1640, 210), (1640, 870), anchor("AcademicGapResult", "left")], "receives", "association", "1", "0..*", (8, -12))

    # Legend
    legend_x, legend_y = 80, 2860
    draw.rounded_rectangle((legend_x, legend_y, 1100, 3110), radius=10, fill="#FFFFFF", outline=LINE, width=2)
    draw.text((legend_x + 16, legend_y + 14), "Legend", font=FONT_TITLE, fill=TEXT)
    draw.text((legend_x + 20, legend_y + 60), "--> association", font=FONT_BODY, fill=TEXT)
    draw.text((legend_x + 20, legend_y + 95), "o-- aggregation", font=FONT_BODY, fill=TEXT)
    draw.text((legend_x + 20, legend_y + 130), "*-- composition", font=FONT_BODY, fill=TEXT)
    draw.text((legend_x + 20, legend_y + 165), "1 / 0..1 / 0..* = multiplicity", font=FONT_BODY, fill=TEXT)
    draw.text((legend_x + 20, legend_y + 205), "Orthogonal connectors are used for readability in the delivered SRS figure.", font=FONT_BODY, fill=TEXT)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
