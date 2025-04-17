# src/llm_utils/models.py
import os
from time import sleep
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import ValidationError
# Ensure FeedbackClassification includes needs_review=False
from src.conn_utils.mongo_conn import FeedbackClassification, FeedbackQuestionnaireSentiment, ListFeedback, ListFeedbackClassification, ListFeedbackQuestionnaire, ListFeedbackQuestionnaireSentiment
from langchain_openai.chat_models.azure import AzureChatOpenAI
from typing import List, Set, Optional, Dict, Any # Added Optional, Dict, Any

# get_llm_model remains the same as the previous version
def get_llm_model():
    use_cloud_llm = int(os.environ.get("USE_CLOUD_LLM", 0)) # Default to 0 (Ollama) if not set
    # Recommendation: Set ARG_TEMPERATURE low (e.g., 0.1 or 0.2) for consistent classification
    temperature = float(os.environ.get("ARG_TEMPERASTURE", 0.2)) # Default to 0.2 if not set
    timeout = int(os.environ.get("ARG_TIMEOUT", 120)) # Default to 120 seconds if not set

    try:
        if use_cloud_llm == 1:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set for Gemini.")
            return ChatGoogleGenerativeAI(model=os.environ.get("GEMINI_MODEL_NAME", "gemini-pro"),
                google_api_key=api_key,
                temperature=temperature,
                timeout=timeout)
        elif use_cloud_llm == 2:
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = os.getenv("OPENAI_API_VERSION")
            deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4o") # Get deployment name
            if not all([azure_endpoint, api_key, api_version, deployment_name]):
                raise ValueError("Azure OpenAI environment variables (ENDPOINT, API_KEY, API_VERSION, DEPLOYMENT_NAME) not fully set.")
            return AzureChatOpenAI(
                deployment_name=deployment_name,
                azure_endpoint=azure_endpoint,
                openai_api_key=api_key,
                api_version=api_version,
                temperature=temperature,
                timeout=timeout)
        else:
            ollama_model = os.environ.get("OLLAMA_MODEL_NAME")
            if not ollama_model:
                 raise ValueError("OLLAMA_MODEL_NAME environment variable not set for Ollama.")
            return OllamaLLM(model=ollama_model, temperature=temperature, timeout=timeout)
    except Exception as e:
        # add_note is deprecated
        raise Exception(f"Error getting LLM model: {e}")


# llm_prompt_chain remains the same
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
        # add_note is deprecated
        raise Exception(f"Error creating LLM prompt chain: {e}")


def feedback_classifier_generic():
    # Updated prompt asking for needs_review flag
    template = """
    Tu és um assistente de IA altamente preciso, especializado em análise e classificação de feedback de clientes em Português de Portugal. A tua tarefa é processar os feedbacks fornecidos e extrair informações específicas estritamente no formato JSON solicitado, indicando se a classificação requer revisão. Responde exclusivamente em Português de Portugal.

    **Objetivo:** Para cada feedback, analisa o conteúdo e preenche a seguinte estrutura JSON:

    ```json
    {{
    "classification": "...", // Classificação *exata* retirada da lista abaixo. NÃO inventar ou modificar.
    "sentiment": "...",      // Sentimento expresso ('Neutral', 'Negative', 'Very Negative').
    "feedback_summary": "...", // Resumo conciso do feedback em Português de Portugal.
    "needs_review": ...      // true se estiveres incerto sobre a classificação OU se o feedback for muito ambíguo, nulo ou dados invalidos, caso contrário false.
    }}
    ```

    **Instruções Detalhadas e Rigorosas:**
    1.  **Leitura:** Lê atentamente cada feedback individualmente.
    2.  **Análise e Preenchimento JSON:**
        * **sentiment:** Determina o sentimento geral. Escolhe OBRIGATORIAMENTE um dos seguintes: 'Neutral', 'Negative', 'Very Negative'.
        * **feedback_summary:** Cria um resumo muito conciso do ponto principal e sugestões. Em Português de Portugal.
        * **classification:** Esta é a parte mais crítica. Segue estas regras ABSOLUTAS:
            * Analisa o tema principal do feedback.
            * Compara esse tema com a lista de classificações fornecida abaixo.
            * Seleciona EXATAMENTE UMA classificação da lista. COPIA A LINHA COMPLETA.
            * **NÃO MODIFIQUES, NÃO ABREVIEES, NÃO INVENTES, NÃO COMBINES classificações.** A classificação no JSON *tem* de corresponder *literalmente* a uma linha da lista.
            * Se vários temas estiverem presentes, foca-te no tema *principal* ou no mais *negativo*.
            * Se tiveres dúvidas significativas sobre qual categoria escolher, ou se o feedback for extremamente vago ou confuso, escolhe a classificação que considerares MAIS PRÓXIMA e define "needs_review" como true. Se nenhuma for minimamente próxima, podes usar uma categoria genérica como "Outros" e define "needs_review" como true.
        * **needs_review:** Define como `true` se:
            * Tiveste dificuldade em escolher a classificação exata.
            * O feedback é muito ambíguo, contraditório ou pouco claro.
            * Escolheste uma categoria genérica por falta de opção específica.
            * Em caso de dados inválidos, ou nulos.
            Define como `false` se tens alta confiança na classificação escolhida.

    **Lista Obrigatória de Classificações (Usar EXATAMENTE como escrito):**
    ----INICIO CLASSIFICAÇÕES----
    {classifications}
    ----FIM CLASSIFICAÇÕES----

    **Exemplos de Como Aplicar as Regras:**

    *Exemplo 1:*
    Feedback: "O serviço de internet falha constantemente. Já liguei várias vezes e a demora na resolução é inaceitável. Preciso disto para trabalhar!"
    JSON Esperado:
    ```json
    {{
    "classification": "Avaria>Demora",
    "sentiment": "Very Negative",
    "feedback_summary": "Cliente reporta falhas constantes na internet e demora na resolução do apoio técnico.",
    "needs_review": false
    }}
    ```

    *Exemplo 2:*
    Feedback: "Fui à loja MEO do Colombo e o atendimento foi 1 estrelas! O funcionário não foi muito simpático e não resolveu o meu problema rapidamente."
    JSON Esperado:
    ```json
    {{
    "classification": "Atendimento>Loja",
    "sentiment": "Very Negative",
    "feedback_summary": "Cliente muito insatisfeito com o atendimento na loja MEO Colombo.",
    "needs_review": false
    }}
    ```

    *Exemplo 3:*
    Feedback: "MEO - Burla com subscrição fraudulenta de serviço "cozinha fácil" \nA empresa "Cozinha Fácil" é fraudulenta e burla clientes da MEO (desconheço se também de outras operadoras) através de falsas subscrições. Nas faturas da MEO de Fevereiro e Março de 2025 constatei que me foram debitados mais de 18€ por uma alegada subscrição que nunca efetuei, tanto mais que só ontem, numa loja da MEO, ouvi falar pela primeira vez desta empresa ou "site". Ainda que desconheça o modus operandi destes burlões, admito que consigam estas falsas subscrições através de comandos de OK ou similares dissimulados nas suas publicidades on-line. Considerando que as várias queixas que consultei relacionadas com esta empresa "Cozinha Fácil" têm todas como lesados clientes da MEO, e considerando que todos os queixosos, e são muitos, negam ter efetuado qualquer subscrição de forma consciente ou deliberada, a vossa empresa não deixa de ter alguma responsabilidade por esta burla, quanto mais não seja por omissão do dever de monitorização e controlo de anunciantes e do dever de proteção dos clientes. Se não for ressarcido, pondero fazer queixa ao MP porque se trata de uma burla na forma qualificada (atento o caráter sistemático da burla e os elevadíssimos montantes obtidos das vítimas com esta prática) e alguém deveria investigar estes criminosos."
    JSON Esperado:
    ```json
    {{
    "classification": "Facturação e saldos>Comunicações>Suspeita de fraude",
    "sentiment": "Very Negative",
    "feedback_summary": "Cliente relata burla através de falsas subscrições do serviço "Cozinha Fácil". Pretende ressarcimento e considera fazer queixa ao MP devido à fraude sistemática.",
    "needs_review": false
    }}
    ```

    *Exemplo 4:*
    Feedback: ""
    JSON Esperado:
    ```json
    {{
    "classification": "Outros",
    "sentiment": None,
    "feedback_summary": None,
    "needs_review": true
    }}
    ```

    *Exemplo 5:*
    Feedback: "Nada"
    JSON Esperado:
    ```json
    {{
    "classification": "Outros",
    "sentiment": None,
    "feedback_summary": None,
    "needs_review": true
    }}
    ```

    **Feedbacks a processar:**
    {feedbacks}

    **Instruções de Formato Adicionais (Obrigatório seguir):**
    {format_instructions}
    """
    # Ensure ListFeedbackClassification's Pydantic definition matches the JSON with needs_review
    return llm_prompt_chain(ListFeedbackClassification, template, ["feedbacks", "classifications"])


# Modified to check classification validity and set needs_review
def process_feedback_generic(chain, feedback_list: ListFeedback, classifications: str, batch_size: int = 10) -> ListFeedbackClassification:
    processed_feedback_list = []
    total_feedbacks = len(feedback_list.list)

    if total_feedbacks < 1 or classifications=="":
        raise ValueError("Process feedback invalid parameters error!")

    # Create a set of valid classifications for efficient lookup
    valid_classifications_set: Set[str] = set(classifications.strip().split('\n'))
    if not valid_classifications_set or (len(valid_classifications_set) == 1 and '' in valid_classifications_set):
         raise ValueError("Valid classifications set is empty. Check database query or content.")
    
    def clean_text(text):
        import re
        """
        Cleans the input text by:
        - Replacing non-breaking spaces and zero-width spaces.
        - Handling both raw and escaped representations of problematic characters.
        """
        # Replace literal non-breaking space (\xa0) with a regular space
        text = text.replace("\xa0", " ")
        
        # Replace literal zero-width space (\u200b) with nothing
        text = text.replace("\u200b", "")
        
        # Handle escaped versions of these characters (e.g., "\\xa0" or "\\u200b")
        text = text.replace("\\xa0", " ").replace("\\u200b", "")
        
        # Optionally, remove other control characters (e.g., ASCII 0-31 except \n and \t)
        #text = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", text)

        text = text.replace("\x80", "€")
        
        # Strip leading/trailing whitespace
        return text.strip()


    for i in range(0, total_feedbacks, batch_size):
        batch = feedback_list.list[i:min(i + batch_size, total_feedbacks)]
        # Prepare batch for prompt (assuming Feedback model has appropriate string representation)
        # Simple example: Join texts. Adjust if Feedback objects need specific formatting.
        batch_texts = [clean_text(str(fb)) for fb in batch]
        # Consider adding identifiers if needed by the prompt or for debugging
        #batch_for_prompt = "\n---\n".join([f"ID_{idx+i}: {text}" for idx, text in enumerate(batch_texts)])
        batch_for_prompt = "\n---\n".join(batch_texts) # Simpler version


        if not batch_for_prompt:
             print(f"Skipping empty batch starting at index {i}")
             continue


        try:
            # Invoke LLM chain
            outputs: ListFeedbackClassification = chain.invoke({
                "feedbacks": batch_for_prompt,
                "classifications": classifications # Pass the single classifications string
            })

            # Post-processing and validation
            if len(outputs.list) == len(batch):
                 for llm_output in outputs.list:
                     
                     llm_output = llm_output.model_dump()
                     
                     # --- Classification Validation ---
                     llm_classification = llm_output["classification"]
                     is_valid_classification = llm_classification in valid_classifications_set

                     # Determine final needs_review status
                     # Mark for review if LLM flagged it OR if classification is invalid/missing
                     final_needs_review = llm_output["needs_review"] or not is_valid_classification or llm_classification is None

                     if not is_valid_classification and llm_classification is not None:
                         print(f"Warning: LLM returned invalid classification '{llm_classification}' for feedback ID {llm_output.get('user_id', 'N/A')}")
                     elif llm_classification is None:
                          print(f"Warning: LLM failed to provide classification for feedback ID {llm_output.get('user_id', 'N/A')}. Marking for review.")

                     llm_output.update({"needs_review": final_needs_review})

                     processed_feedback_list.append(FeedbackClassification(**llm_output))

            else:
                print(f"Warning: Mismatch between input batch size ({len(batch)}) and LLM output size ({len(outputs.list)}) for batch starting at index {i}. Skipping batch.")
                # Log details of the batch and output for debugging


        except Exception as e:
            print(f"Error processing batch starting at index {i}: {e}")
            # Mark all items in this failed batch as needing review?
            for original_feedback in batch:
                 error_data = original_feedback.model_dump()
                 error_data.update({
                     "feedback_summary": f"Error during processing: {e}",
                     "classification": "None",
                     "sentiment": "None",
                     "needs_review": True
                 })
                 try:
                      processed_item = FeedbackClassification(**error_data)
                      processed_feedback_list.append(processed_item)
                 except Exception as validation_error:
                      print(f"Validation Error creating error feedback object: {validation_error}. Data: {error_data}")

            sleep(1) # Simple retry delay

    # Return a single list containing all processed items, flagged as needed
    return ListFeedbackClassification(list=processed_feedback_list)


# --- New Sentiment Analysis Functions ---

def feedback_sentiment_analyzer():
    """
    Creates an LLM chain specifically for sentiment analysis based on the user's requirements.
    Includes few-shot examples for invalid feedback handling.
    """

    template = """
    Tu és um assistente de IA preciso, especializado em análise de sentimento de feedback de clientes em Português de Portugal, especificamente para a questão "O que podera a MEO fazer para melhorar o atendimento?". A tua tarefa é determinar o sentimento expresso no feedback.

    **Objetivo:** Para cada feedback, analisa o conteúdo e determina o sentimento, respondendo estritamente no formato JSON solicitado.

    **Formato JSON de Saída Esperado (para cada feedback):**

    ```json
    {{
      "sentiment": "..." // Deve ser 'Very Negative', 'Negative', 'Neutral', ou null (literalmente a palavra null, não a string "null")
    }}
    ```

    **Instruções Detalhadas:**
    1.  **Leitura:** Lê atentamente cada feedback individualmente. O feedback responde à pergunta: "O que podera a MEO fazer para melhorar o atendimento?".
    2.  **Análise de Sentimento:**
        * Avalia se o feedback expressa uma opinião muito negativa, negativa ou neutra sobre a melhoria do atendimento.
        * **'Very Negative':** Indica insatisfação extrema, críticas fortes, problemas graves ou sugestões dadas de forma muito negativa.
        * **'Negative':** Indica insatisfação, críticas, problemas ou sugestões dadas de forma negativa.
        * **'Neutral':** Indica uma declaração objetiva, sem carga emocional clara, ou um comentário que não expressa uma opinião direta sobre a melhoria (ex: "Não sei", "Não tenho sugestões").
    3.  **Tratamento de Feedback Inválido:**
        * Se o feedback for vazio (''), muito curto e sem sentido (ex: '.', 'na', '0'), ou indicar explicitamente que não há feedback (ex: 'Nada', 'N/A', 'Sem comentários'), o sentimento deve ser `null`.
    4.  **Formato de Saída:** Retorna a tua análise *apenas* no formato JSON especificado acima.

    **Exemplos de Casos Válidos:**

    *Feedback:* "Assegurar PDO disponível antes da deslocação do técnico para instalação do serviço em nova morada."
    *JSON Esperado:*
    ```json
    {{
      "sentiment": "Negative"
    }}
    ```
    *(Implica uma falha ou área a melhorar)*

    *Feedback:* "Péssimo serviço, nunca mais!"
     *JSON Esperado:*
    ```json
    {{
      "sentiment": "Very Negative"
    }}
    ```

    *Feedback:* "Ter seguro nos telemóveis que empresta em vez de tentar fazer negócio com azares que podem acontecer."
    *JSON Esperado:*
    ```json
    {{
      "sentiment": "Negative"
    }}
    ```
    *(Crítica a uma prática)*

    *Feedback:* "Não tenho tido problemas recentemente."
    *JSON Esperado:*
    ```json
    {{
      "sentiment": "Neutral"
    }}
    ```
    *(Declaração factual sem forte carga sobre *melhoria*)*

    **Exemplos de Casos Inválidos (Resultando em `null`):**

    *Feedback:* " " (string com espaço)
    *JSON Esperado:*
    ```json
    {{
      "sentiment": null
    }}
    ```

    *Feedback:* "Nada"
    *JSON Esperado:*
    ```json
    {{
      "sentiment": null
    }}
    ```

    *Feedback:* "."
    *JSON Esperado:*
    ```json
    {{
      "sentiment": null
    }}
    ```

    *Feedback:* "na"
    *JSON Esperado:*
    ```json
    {{
      "sentiment": null
    }}
    ```

    *Feedback:* "0"
    *JSON Esperado:*
    ```json
    {{
      "sentiment": null
    }}
    ```

    **Feedbacks a processar:**
    {feedbacks}

    **Instruções de Formato Adicionais (Obrigatório seguir):**
    {format_instructions}
    """
    # Use the ListFeedbackQuestionnaireSentiment Pydantic model for parsing
    # Ensure this model exists and allows sentiment: Optional[str] with values 'Very Negative', 'Negative', 'Neutral'
    return llm_prompt_chain(ListFeedbackQuestionnaireSentiment, template, ["feedbacks"])


# Corrected batch processing function for sentiment analysis (No pre-filtering)
def process_feedback_sentiment(chain, feedback_list: ListFeedbackQuestionnaire, batch_size: int = 10) -> ListFeedbackQuestionnaireSentiment:

    validated_output_items = [] # List to hold validated FeedbackQuestionnaireOutput objects
    total_feedbacks = len(feedback_list.list)

    if total_feedbacks < 1:
        raise ValueError("Process feedback sentiment invalid parameters error!")


    for i in range(0, total_feedbacks, batch_size):
        batch_input_items = feedback_list.list[i:min(i + batch_size, total_feedbacks)]
        if not batch_input_items:
            print(f"Batch {i // batch_size + 1}: Skipped empty batch.")
            continue

        # Store original data dictionaries for merging later
        original_data_batch = [item.model_dump() for item in batch_input_items]
        # Prepare batch text for LLM prompt using the 'feedback' field
        batch_texts = [str(item) for item in batch_input_items]
        batch_for_prompt = "\n---\n".join(batch_texts) # Match format if needed by prompt

        if not batch_for_prompt:
             print(f"Skipping effectively empty batch starting at index {i} after cleaning.")
             # Handle empty items by creating default error entries if desired
             # (Similar logic as in process_feedback_generic's handling of empty batch)
             for original_data in original_data_batch:
                 error_data = {**original_data, 'sentiment': 'Error: Input feedback was empty or invalid after cleaning'}
                 try:
                    # Validate even the error entry against the output model
                    validated_item = FeedbackQuestionnaireSentiment(**error_data)
                    validated_output_items.append(validated_item)
                 except ValidationError as val_err:
                    print(f"Validation Error creating default error feedback object: {val_err}. Data: {error_data}")
             continue

        try:
            # Invoke LLM chain (sentiment analyzer)
            # Ensure chain's parser is ListFeedbackQuestionnaireSentiment
            outputs: ListFeedbackQuestionnaireSentiment = chain.invoke({
                "feedbacks": batch_for_prompt
                # No 'classifications' needed here
            })

            # Post-processing: Merge and Validate
            if outputs.list and len(outputs.list) != len(batch_input_items):
                # Handle mismatch between input batch size and LLM output size
                print(f"Warning: Mismatch between input batch size. Marking items as 'Error'.")
                for original_data in original_data_batch:
                    error_data = {**original_data, 'sentiment': 'Error: LLM output count mismatch'}
                    try:
                        validated_item = FeedbackQuestionnaireSentiment(**error_data)
                        validated_output_items.append(validated_item)
                    except ValidationError as val_err:
                        print(f"Validation Error creating mismatch error feedback object: {val_err}. Data: {error_data}")
            else:
                validated_output_items.extend(outputs.list)
        # Catch Pydantic errors during invoke/parsing (if model used for parsing is wrong)
        except ValidationError as pydantic_err:
            print(f"Pydantic Validation Error during LLM Parsing in batch {i // batch_size + 1}: {pydantic_err}")
            for original_data in original_data_batch:
                error_data = {**original_data, 'sentiment': "Error"}
                try:
                    validated_item = FeedbackQuestionnaireSentiment(**error_data)
                    validated_output_items.append(validated_item)
                except ValidationError as val_err:
                    print(f"Validation Error creating parsing error feedback object: {val_err}. Data: {error_data}")
            sleep(1)
        # Catch other general exceptions
        except Exception as e:
            print(f"General Error processing LLM batch {i // batch_size + 1}: {e}")
            for original_data in original_data_batch:
                 error_data = {**original_data, 'sentiment': "Error"}
                 try:
                      validated_item = FeedbackQuestionnaireSentiment(**error_data)
                      validated_output_items.append(validated_item)
                 except ValidationError as val_err:
                      print(f"Validation Error creating general error feedback object: {val_err}. Data: {error_data}")
            sleep(1)

    # Return the list wrapped in the Pydantic list model
    return ListFeedbackQuestionnaireSentiment(list=validated_output_items)


# Presumed location: app-copy/backend/src/llm_utils/models.py
# (Make sure necessary imports like BaseModel, Field, List, llm_prompt_chain are present)

from pydantic import BaseModel, Field
from typing import List, Optional # Added Optional for potential future use

# Assume llm_prompt_chain is defined elsewhere in this file or imported
# from .some_module import llm_prompt_chain # Example import


# --- Define Pydantic Models with ENGLISH Field Names ---

class EmergingTopic(BaseModel): # Renamed from TemaEmergente
    topic: str = Field(description="The identified topic or theme that is relevant but infrequent.")
    justification: str = Field(description="Brief explanation why this topic is important despite low frequency (e.g., strong emotion, new trend, strategic impact). Max 40 words.")

class FeedbackReportOutputEN(BaseModel): # Renamed from FeedbackReportOutput
    customer_suggestions: List[str] = Field(description="List of the main concrete suggestions given by customers for improvement (max 50 words per suggestion).")
    ai_improvement_proposals: List[str] = Field(description="List of actionable improvement proposals, based on overall feedback and emerging topics (max 50 words per proposal).")
    emerging_topics: List[EmergingTopic] = Field(description="List of relevant but infrequent topics identified in the feedback.")

# --- Updated feedback_report Function ---

def feedback_report():

    # Instructions remain in Portuguese to guide analysis of Portuguese text
    template = """
    Você é um analista de feedback de clientes especializado em analisar respostas à pergunta 'O que poderá a MEO fazer para melhorar o serviço ao cliente?' provenientes de questionários de satisfação de uma empresa de telecomunicações em Portugal. O seu foco é extrair sugestões concretas, temas emergentes e propostas de melhoria diretamente dessas respostas.

    A sua tarefa é analisar os dados de feedback fornecidos (respostas à pergunta 'O que poderá a MEO fazer para melhorar o serviço ao cliente?') e gerar um relatório JSON conciso que destaque sugestões diretas dos clientes, as suas recomendações de melhoria e temas importantes mas menos frequentes. A estrutura do JSON final deve usar os nomes de campo em Inglês especificados abaixo.

    **Instruções:** Responde sempre em Português de Portugal para as descrições e sugestões. Seja conciso e direto nas suas respostas.

    1.  **Leia as Respostas ao Questionário:** Analise o conjunto de respostas fornecidas à pergunta 'O que poderá a MEO fazer para melhorar o serviço ao cliente?'.

    2.  **Extraia Informações Chave:** Com base na sua análise, identifique o seguinte:

        * **2.1. Sugestões dos Clientes (customer_suggestions):** Identifique e liste as sugestões de melhoria mais concretas e recorrentes mencionadas diretamente pelos clientes nas suas respostas. Limite cada sugestão a cerca de 50 palavras. Ordene pela frequência ou importância percebida. O conteúdo das sugestões deve estar em Português.

        * **2.2. Temas Emergentes (emerging_topics):** Identifique entre tópicos ou temas que, apesar de não serem os mais frequentes em volume nas respostas, são importantes por outras razões (ex: emoção forte, novas tendências, impacto estratégico, recclamações específicas, etc.).
            * **Para cada tema emergente, forneça o tópico ("topic") em Português e uma breve justificativa ("justification") em Português (máximo 40 palavras) explicando a sua importância.**

        * **2.3. Propostas de Melhoria (ai_improvement_proposals):** Com base nas respostas analisadas, sugira um plano de propostas de melhoria acionáveis para os serviços ou atendimento ao cliente. Seja específico (problema/solução). Limite cada proposta a cerca de 50 palavras. O conteúdo das propostas deve estar em Português.

    3.  **Gere a Saída JSON (com campos em Inglês):** Retorne **exclusivamente** um objeto JSON válido com a seguinte estrutura **EM INGLÊS**. O *conteúdo* das strings (sugestões, tópicos, justificativas, propostas) deve permanecer em Português.

        ```json
        {{
            "customer_suggestions": [
                "Sugestão concreta do cliente 1...",
                "Sugestão concreta do cliente 2...",
                "Sugestão concreta do cliente 3...",
                mais sugestões
            ],
            "emerging_topics": [
                {{
                    "topic": "Tópico pouco frequente mas importante 1",
                    "justification": "Justificativa breve em Português..."
                }},
                {{
                    "topic": "Tópico pouco frequente mas importante 2",
                    "justification": "Justificativa breve em Português..."
                }},
                more tópicos
            ],
            "ai_improvement_proposals": [
                "Ação específica sugerida pela IA 1 em Português...",
                "Ação específica sugerida pela IA 2 em Português...",
                mais melhorias
            ]
        }}
        ```

    4.  **Respostas à Pergunta 'O que podemos melhorar?':**
        {data_str}

    5.  **Instruções de Formato de Saída (Obrigatório Seguir):**
        {format_instructions}

    """

    try:
        # Pass the RENAMED Pydantic model for parsing
        return llm_prompt_chain(FeedbackReportOutputEN, template, ["data_str"])
    except Exception as e:
        print(f"Error creating report prompt chain: {e}")
        raise Exception(f"Error creating report prompt chain: {e}")


# --- Updated process_report function ---

def process_report(chain, data_str):
    """
    Invokes the LLM chain to process the feedback data string.
    """
    if data_str=="":
        raise ValueError("Process report invalid parameters error!")
    try:
        # Update type hint to use the renamed Pydantic model
        output: FeedbackReportOutputEN = chain.invoke({"data_str": data_str})
        return output
    except Exception as e:
        print(f"Error processing report: {e}")
        raise Exception(f"Error processing report: {e}")