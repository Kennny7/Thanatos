# Thanatos/services/document/pdf_generator.py
"""
PDF Generation Service for Thanatos.
Converts resumes (from LaTeX / Markdown / Structured Profiles) and cover letters
into professional, beautiful PDF attachments using ReportLab.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, KeepTogether
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)


def clean_latex_to_text(tex_content: str) -> str:
    """Strip LaTeX commands and syntax into clean plain text for conversion."""
    text = tex_content
    # Remove comments
    text = re.sub(r"%.*$", "", text, flags=re.MULTILINE)
    # Remove documentclass, usepackage, etc.
    text = re.sub(r"\\documentclass\[.*?\]\{.*?\}", "", text)
    text = re.sub(r"\\usepackage\[.*?\]\{.*?\}", "", text)
    text = re.sub(r"\\usepackage\{.*?\}", "", text)
    text = re.sub(r"\\renewcommand\{.*?\}\{.*?\}", "", text)
    text = re.sub(r"\\setlist\[.*?\]\{.*?\}", "", text)
    text = re.sub(r"\\setlength\{.*?\}\{.*?\}", "", text)
    text = re.sub(r"\\titleformat.*", "", text)
    text = re.sub(r"\\titlespacing.*", "", text)
    text = re.sub(r"\\newcommand.*", "", text)
    text = re.sub(r"\\begin\{document\}", "", text)
    text = re.sub(r"\\end\{document\}", "", text)
    text = re.sub(r"\\begin\{itemize\}", "", text)
    text = re.sub(r"\\end\{itemize\}", "", text)
    text = re.sub(r"\\begin\{description\}", "", text)
    text = re.sub(r"\\end\{description\}", "", text)
    text = re.sub(r"\\begin\{center\}", "", text)
    text = re.sub(r"\\end\{center\}", "", text)
    # Replace \item[Heading:] with Heading:
    text = re.sub(r"\\item\[(.*?)\]", r"\1 ", text)
    text = re.sub(r"\\item", "•", text)
    # Replace \section*{Name} with Section: Name
    text = re.sub(r"\\section\*?\{([^}]+)\}", r"### \1", text)
    # Replace \textbf{text} with <b>text</b>
    text = re.sub(r"\\textbf\{([^}]+)\}", r"<b>\1</b>", text)
    # Replace \textit{text} with <i>text</i>
    text = re.sub(r"\\textit\{([^}]+)\}", r"<i>\1</i>", text)
    # Replace \href{url}{label} with label (url)
    text = re.sub(r"\\href\{([^}]+)\}\{([^}]+)\}", r"<font color='#0066cc'><u>\2</u></font>", text)
    # Replace rules and spaces
    text = re.sub(r"\\sectionline", "", text)
    text = re.sub(r"\\hr", "", text)
    text = re.sub(r"\\vspace\{.*?\}", "", text)
    text = re.sub(r"\\textbullet", "•", text)
    text = re.sub(r"\\,", " ", text)
    text = re.sub(r"\\\[.*?\]", "", text)
    text = re.sub(r"\\\\", "\n", text)
    return text.strip()


class PDFGenerator:
    """Generates elegant, industry-standard PDF resumes and cover letters."""

    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        self.title_style = ParagraphStyle(
            "DocTitle",
            parent=self.styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            alignment=1,  # Center
            spaceAfter=4,
        )
        self.subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=self.styles["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0284c7"),
            fontName="Helvetica-Bold",
            alignment=1,  # Center
            spaceAfter=6,
        )
        self.meta_style = ParagraphStyle(
            "DocMeta",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748b"),
            alignment=1,  # Center
            spaceAfter=10,
        )
        self.section_heading = ParagraphStyle(
            "DocSectionHeading",
            parent=self.styles["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceBefore=8,
            spaceAfter=3,
        )
        self.body_style = ParagraphStyle(
            "DocBody",
            parent=self.styles["Normal"],
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#334155"),
            fontName="Helvetica",
            spaceAfter=6,
        )
        self.bullet_style = ParagraphStyle(
            "DocBullet",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            fontName="Helvetica",
            leftIndent=15,
            spaceAfter=3,
        )

    def generate_cover_letter_pdf(
        self,
        cover_letter_text: str,
        applicant_name: str,
        job_title: str,
        company: str,
        output_pdf_path: str,
        contact_info: Optional[Dict[str, str]] = None,
    ) -> str:
        """Create a professional, humanized cover letter PDF document."""
        os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=A4,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        elements = []
        # Header
        elements.append(Paragraph(applicant_name, self.title_style))
        if contact_info:
            contact_line = f"{contact_info.get('email', '')} • {contact_info.get('phone', '')} • {contact_info.get('location', '')}"
            elements.append(Paragraph(contact_line, self.meta_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=14))

        # Recipient line
        elements.append(Paragraph(f"<b>Application:</b> {job_title} at {company}", self.subtitle_style))
        elements.append(Spacer(1, 10))

        # Body paragraphs
        lines = cover_letter_text.strip().split("\n")
        current_para = []
        for line in lines:
            line = line.strip()
            if not line:
                if current_para:
                    text_block = " ".join(current_para)
                    # Convert markdown bold to reportlab bold
                    text_block = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text_block)
                    elements.append(Paragraph(text_block, self.body_style))
                    current_para = []
            else:
                current_para.append(line)
        if current_para:
            text_block = " ".join(current_para)
            text_block = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text_block)
            elements.append(Paragraph(text_block, self.body_style))

        doc.build(elements)
        logger.info("Generated Cover Letter PDF at: %s", output_pdf_path)
        return output_pdf_path

    def generate_resume_pdf(
        self,
        source_tex_or_md: str,
        output_pdf_path: str,
        candidate_name: str = "Khushal Pareta",
        candidate_title: str = "AI Developer | Machine Learning Engineer",
        candidate_contacts: Optional[Dict[str, str]] = None,
    ) -> str:
        """Create a professional multi-section Resume PDF from LaTeX/Markdown source."""
        os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=A4,
            leftMargin=0.6 * inch,
            rightMargin=0.6 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
        )

        elements = []

        # 1. Header
        elements.append(Paragraph(candidate_name, self.title_style))
        elements.append(Paragraph(candidate_title, self.subtitle_style))

        contacts_str = "Khushalpareta9@gmail.com • +91 96604 64021 • Mumbai, India"
        if candidate_contacts:
            email = candidate_contacts.get("email", "Khushalpareta9@gmail.com")
            phone = candidate_contacts.get("phone", "+91 96604 64021")
            loc = candidate_contacts.get("location", "Mumbai, India")
            contacts_str = f"{email} • {phone} • {loc}"
        elements.append(Paragraph(contacts_str, self.meta_style))

        # Links
        links_str = "<b>GitHub:</b> github.com/Kennny7  •  <b>LinkedIn:</b> linkedin.com/in/khushal-pareta  •  <b>Portfolio:</b> kennny7.github.io"
        elements.append(Paragraph(links_str, self.meta_style))
        elements.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#0284c7"), spaceAfter=10))

        # 2. Parse body text
        cleaned_text = clean_latex_to_text(source_tex_or_md)
        lines = cleaned_text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Heading
            if line.startswith("### ") or line.startswith("## "):
                heading_name = line.replace("#", "").strip()
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(heading_name, self.section_heading))
                elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceAfter=4))
            elif line.startswith("•") or line.startswith("-") or line.startswith("*"):
                bullet_content = line.lstrip("•-* ").strip()
                bullet_content = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", bullet_content)
                elements.append(Paragraph(f"• {bullet_content}", self.bullet_style))
            else:
                line_content = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)
                elements.append(Paragraph(line_content, self.body_style))

        doc.build(elements)
        logger.info("Generated Resume PDF at: %s", output_pdf_path)
        return output_pdf_path


# Singleton PDF generator
pdf_generator = PDFGenerator()
