import fitz

def check_signatures(pdf_path):
    signature_issues = []
    signed_pages = []

    with open(pdf_path, "rb") as f:
        raw_data = f.read()
        signature_tag_found = any(tag in raw_data for tag in [
            b"<</Subtype/page/Type/FillSignData>>", b"/Sig", b"/Signature", b"/FillSignData"
        ])
    with fitz.open(pdf_path) as doc:
        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text().lower()
            page_number = i + 1
            if "signature" in text and not signature_tag_found:
                if page_number != 1:
                    signature_issues.append(f"Signature missing on Page {page_number}")
            elif "signature" in text and signature_tag_found:
                if page_number != 1:
                    signed_pages.append(page_number)
    if signature_issues:
        print("Signature issues found:")
        for issue in signature_issues:
            print(issue)
    else:
        print("All expected signature fields appear to be signed.")
    if signed_pages:
        for page_num in signed_pages:
            print(f"Page {page_num} appears signed.")
    return signature_issues

pdf_path = str(input("put the path pls: "))

check_signatures(pdf_path)
