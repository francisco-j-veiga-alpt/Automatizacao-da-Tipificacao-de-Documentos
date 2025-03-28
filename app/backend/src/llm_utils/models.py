import os
from time import sleep
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from src.conn_utils.mongo_conn import FeedbackClassification, ListFeedback, ListFeedbackClassification
from langchain_openai.chat_models.azure import AzureChatOpenAI
from typing import List

def get_llm_model():
    use_cloud_llm = int(os.environ.get("USE_CLOUD_LLM"))
    temperature = float(os.environ.get("ARG_TEMPERASTURE"))
    timeout = int(os.environ.get("ARG_TIMEOUT"))

    try:
        if use_cloud_llm == 1:
            return ChatGoogleGenerativeAI(model=os.environ.get("GEMINI_MODEL_NAME"), 
                google_api_key=os.environ.get("GOOGLE_API_KEY"), 
                temperature=temperature, 
                timeout=timeout)
        elif use_cloud_llm == 2:
            return AzureChatOpenAI(
                deployment_name="gpt-4o",  # Replace with your deployment name
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("OPENAI_API_VERSION"),
                temperature=temperature, 
                timeout=timeout)
        else:
            return OllamaLLM(model=os.environ.get("OLLAMA_MODEL_NAME"), temperature=temperature, timeout=timeout)
    except Exception as e:
        e.add_note(f"Error llm model: {e}")
        raise


def llm_prompt_chain(pydantic_object, template, input_variables):
    try:

        llm = get_llm_model()

        parser = PydanticOutputParser(pydantic_object=pydantic_object)

        prompt = PromptTemplate(
            template=template,
            input_variables=input_variables,
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | llm | parser

        return chain
    except Exception as e:
        e.add_note(f"Error cllm prompt chain: {e}")
        raise


def feedback_classifier_generic():
    template = """
    Tu és um assistente de IA especializado em análise e classificação de feedback de clientes. A tua tarefa é processar os feedbacks fornecidos e extrair informações específicas em formato JSON. Responde exclusivamente em Português de Portugal.

    **Objetivo:** Para cada feedback fornecido, analisa o seu conteúdo e preenche a seguinte estrutura JSON:

    ```json
    {{
    "classification": "...", // Classificação *exata* retirada da lista abaixo.
    "sentiment": "...",      // Sentimento expresso ('Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative').
    "feedback_summary": "..." // Resumo conciso do feedback em Português de Portugal.
    }}

    Instruções Detalhadas:
    Leitura: Lê atentamente cada feedback individualmente.
    Análise e Preenchimento JSON: Para cada feedback, preenche os campos do JSON:
    sentiment: Determina o sentimento geral expresso no feedback. Escolhe obrigatoriamente um dos seguintes valores: 'Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative'.
    feedback_summary: Cria um resumo conciso do ponto principal do feedback e de quaisquer sugestões mencionadas. O resumo deve estar em Português de Portugal.
    classification: Esta é a parte mais crítica.
    Analisa o conteúdo principal do feedback (refletido no teu resumo).
    Compara o tema principal com a lista de classificações fornecida abaixo, entre "----INICIO CLASSIFICAÇÕES----" e "---FIM CLASSIFICAÇÕES----".
    REGRA ABSOLUTA: Deves selecionar EXATAMENTE UMA das classificações presentes na lista abaixo. Copia a linha completa da classificação escolhida, incluindo os '>' se existirem.
    NÃO MODIFIQUES, NÃO ABREVIEES, NÃO INVENTES nenhuma classificação. A classificação no JSON tem de corresponder literalmente a uma das linhas da lista.
    A estrutura hierárquica (indicada por '>') serve para entender o contexto da classificação (ex: "Adesão ou Activação > Serviços Internet > Demora"), mas deves copiar a linha inteira como a classificação final.
    
    Lista Obrigatória de Classificações:
    ----INICIO CLASSIFICAÇÕES----
    {classifications}
    ----FIM CLASSIFICAÇÕES----

    Linguagem: Toda a tua resposta, incluindo o JSON e os resumos, deve ser em Português de Portugal.

    Feedbacks a processar:
    {feedbacks}

    Instruções de Formato Adicionais:
    {format_instructions}
    """
    return llm_prompt_chain(ListFeedbackClassification, template, ["feedbacks", "classifications"])



def process_feedback_generic(chain, feedback_list: ListFeedback, classifications: List[str], batch_size: int = 10):
    try:
        processed_feedback = []

        for i in range(0, len(feedback_list.list), batch_size):
            batch = feedback_list.list[i:i + batch_size]

            outputs = chain.invoke({
                "feedbacks": batch,
                "classifications": classifications
            })

            processed_feedback.extend(outputs.list)

        return ListFeedbackClassification(list=processed_feedback)

    except Exception as e:
        raise Exception(f"Error processing feedback: {e}")





