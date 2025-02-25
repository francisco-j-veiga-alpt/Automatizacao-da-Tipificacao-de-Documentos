from pymongo import MongoClient
from pydantic import BaseModel, RootModel, Field, field_validator, model_validator
from typing import List, Dict, Optional
from src.utils.utils import parse_date
from datetime import timedelta, datetime, date, time


class InputPostPortalDaQuiexa(BaseModel):
    to_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.combine(datetime.today().date(), time.min), description="Get feedback until to_date (exclusive)"
    )
    last_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.combine(datetime.today().date(), time.min) - timedelta(2),
        description="Last date feedback was processed",
    )
    begin_pages_to_look: int = Field(
        1, ge=1, description="Strat page to look for in the feedback pages"
    )
    num_of_pages_to_look: int = Field(
        5, ge=2, description="Number of pages to look for in the feedback pages"
    )
    delete_feedback: bool = Field(
        False, description="Delete any existing feedback prior to insertion between dates"
    )

    @model_validator(mode="after")
    def check_date_relationship(cls, values: "InputPostPortalDaQuiexa"):
        """Ensures to_date is greater than last_date + 1 day."""
        if values.last_date is not None and values.to_date is not None:
            if values.to_date <= values.last_date + timedelta(days=1):
                raise ValueError(
                    "to_date must be greater than last_date + 1 day"
                )
        return values


class FeedbackPortalDaQuiexa(BaseModel):
    data: datetime = Field(description="Data do feedback")
    utilizador: str = Field(description="Nome do utilizador na plataforma")
    titulo: str = Field(description="Titulo do feedback")
    feedback: str = Field(description="Feedback do utilizador.")
    # TODO: metadata- rede social de consumidores online


class ListFeedbackPortalDaQuiexa(RootModel[List[FeedbackPortalDaQuiexa]]):
    root: List[FeedbackPortalDaQuiexa]


class FeedbackClassificationPortalDaQuiexa(BaseModel):
    area_de_feedback: str = Field(description="Area que o clente reclama")
    classificacao: str = Field(description="A classe principal do feedback")
    assunto: str = Field(description="Assunto do feedback")
    sentimento: str = Field(description="O sentimento expresso no feedback ('Positivo', 'Negativo', or 'Neutro').")
    resumo: str = Field(description="O resumo do feedback")
    urgente: str = Field(description="Se assunto é urgente('Sim', 'Não)?")

    @field_validator("sentimento")
    def sentiment_must_be_valid(cls, value):
        if value.lower() not in ["positivo", "negativo", "neutro"]:
            raise ValueError("Sentiment tem de ser 'Positivo', 'Negativo', or 'Neutro'")
        return value.title()


    @field_validator("urgente")
    def urgente_must_be_valid(cls, value):
        if value.lower() not in ["sim", "não"]:
            raise ValueError("Urgente tem de ser 'Sim', 'Não")
        return value.title()


class CollectionPortalDaQuixa(FeedbackPortalDaQuiexa, FeedbackClassificationPortalDaQuiexa):
    pass


class ListCollectionPortalDaQuixa(RootModel[List[CollectionPortalDaQuixa]]):
    root: List[CollectionPortalDaQuixa]

class RelatorioMensal(BaseModel):
    mes: str = Field(..., description="Nome do Mês")
    ano: int = Field(..., description="Ano")
    resumo: str = Field(..., description="Visão geral concisa dos principais problemas")
    acoes_sugeridas: List[str] = Field(..., description="Lista de ações sugeridas")
    


def connect_to_collection(conn_str, db_name, collection_name):
    try:
        client = MongoClient(conn_str)
        db = client[db_name]

        if collection_name not in db.list_collection_names():
            raise ValueError(f"Collection '{collection_name}' does not exist.")

        collection = db[collection_name]
        return collection, client
    except Exception as e:
        e.add_note(f"MongoDB connection error: {e}")
        raise


def insert_data(collection, feed: List[Dict] | Dict):
    try:
        if isinstance(feed, list):
            result = collection.insert_many(feed)
            return [str(res) for res in result.inserted_ids]
        else:
            result = collection.insert_one(feed)
            return str(result.inserted_id)
    except e:
        e.add_note(f"Error inserting data: {e}")
        raise


def delete_data_between_dates(collection, start_date, end_date, date_field):

    try:
        if not (isinstance(start_date, datetime) and isinstance(start_date, datetime)) :
            raise ValueError("start_date + delta 1 must be earlier than end_date.")

        if start_date + timedelta(days=1) >= end_date:
            raise ValueError("start_date + delta 1 must be earlier than end_date.")
        
        query = {
            date_field: {"$gt": start_date, "$lt": end_date}
        }

        result = collection.delete_many(query)
        return result.deleted_count
        
    except e:
        e.add_note(f"An error occurred when deleting data: {e}")
        raise


def get_data_by_year_month(collection, year, month):
    try:
        today = date.today()
        if year > today.year:
            raise ValueError("Invalid Year!")
        elif year == today.year and month > today.month:
            raise ValueError("Invalid Month!")
        elif month < 1 and month > 12:
            raise ValueError("Invalid Month!")

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        pipeline = [
            {
                '$match': {
                    'data': {
                        '$gte': start_date,
                        '$lt': end_date
                    }
                }
            },
            {
                '$sort': {'data': 1}
            },
            {
                '$project': {
                    '_id': 0,
                    'area_de_feedback': 1,
                    'classificacao': 1,
                    'assunto': 1,
                    'sentimento': 1,
                    'resumo': 1,
                    'urgente': 1
                }
            }
        ]

        return {
            "mes": month,
            "ano": year,
            "feedbacks": list(collection.aggregate(pipeline))
        }
    except Exception as e:
        e.add_note(f"Get monthly feedback error: {e}")
        raise







