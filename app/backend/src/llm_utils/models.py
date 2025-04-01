# src/llm_utils/models.py
import os
from time import sleep
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
# Ensure FeedbackClassification includes needs_review=False
from src.conn_utils.mongo_conn import FeedbackClassification, ListFeedback, ListFeedbackClassification
from langchain_openai.chat_models.azure import AzureChatOpenAI
from typing import List, Set

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
    "feedback_summary": None",
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
    "feedback_summary": None",
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

