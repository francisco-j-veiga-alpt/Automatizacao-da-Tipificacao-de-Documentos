import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pydantic import ValidationError
from src.utils.utils import string_to_date
from src.conn_utils.mongo_conn import FeedbackPortalDaQuiexa, InputPostPortalDaQuiexa, ListFeedbackPortalDaQuiexa

def prep_feedback_portal_da_queixa(feedback: FeedbackPortalDaQuiexa):
    return feedback.titulo + "\n" + feedback.feedback

def get_portal_da_queixa_feedback(params: InputPostPortalDaQuiexa):

    try:
        page_url = os.environ.get("URL_PORTAL_DA_QUEIXA_COMPLAINTS")
        pages_url = [page_url + "?p=" + str(num) for num in range(params.begin_pages_to_look, params.begin_pages_to_look + params.num_of_pages_to_look + 1)]

        feedback_meta = set()

        for page_url in pages_url:
            try:
                response = requests.get(page_url, verify=False, timeout=30, proxies = { "https" : os.environ.get("PROXY")})
            except Exception as e:
                e.add_note(f"Error request call: {e}")
                raise
            response.raise_for_status()
            soup_parser = BeautifulSoup(response.text, 'html.parser')
            page_complaints_url = soup_parser.find_all(class_='card brand-content-card')
            for page in page_complaints_url:
                date_str = page.find_all(class_='col-12 brand-detail__complaints-list__item-date')[0].text
                temp_date = string_to_date(date_str)

                if temp_date and temp_date < params.to_date and temp_date > params.last_date:
                    feedback_meta.add((page['href'], temp_date))

        if not feedback_meta:
            raise ValueError("Feedback Meta empty!")
    except Exception as e:
        e.add_note(f"Error during requests step 1: {e}")
        raise

    try:
        feedback_data = []

        for url, complaint_date in feedback_meta:
            response = requests.get(url, verify=False, timeout=30, proxies = { "https" : os.environ.get("PROXY")})
            response.raise_for_status()
            soup_parser = BeautifulSoup(response.text, 'html.parser')
            page_complaints_url = soup_parser.find_all(class_='card card--user')

            if page_complaints_url:
                try:
                    customer_name = page_complaints_url[0].find_all(class_='complaint-detail__complaint-body-item-avatar rounded-circle border shadow-sm')[0]['alt']
                    complaint_title = soup_parser.find_all(class_='complaint-detail__title')[0].text
                    complaint_text = ""
                    for child in page_complaints_url[0].find_all_next('div', class_='card-body')[0].children:
                        if isinstance(child, str):
                            if len(child.strip()) == 0:
                                complaint_text = complaint_text + " "
                            else:
                                complaint_text = complaint_text + child.strip()
                    data = {
                        "data": complaint_date,
                        "utilizador": customer_name,
                        "titulo": complaint_title,
                        "feedback": complaint_text
                    }
                    try:
                        feedback = FeedbackPortalDaQuiexa.model_validate(data)
                        feedback_data.append(feedback)
                    except ValidationError as e:
                        e.add_note(f"Validation Error with feedback: {e}")
                        raise
                except Exception as e:
                    e.add_note(f"Error extracting data from URL: {url}")
                    raise
            else:
                raise ValueError(f"No complaint details found for URL: {url}")
        if len(feedback_data) == 0:
            raise ValueError("Feedback Data empty!")
        return ListFeedbackPortalDaQuiexa(root=feedback_data)
    except Exception as e:
        e.add_note(f"Error during requests step 2: {e}")
        raise
