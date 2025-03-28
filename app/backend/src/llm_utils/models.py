# src/llm_utils/models.py
import os
from time import sleep
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from src.conn_utils.mongo_conn import FeedbackClassification, ListFeedback, ListFeedbackClassification # Assuming mongo_conn defines these
from langchain_openai.chat_models.azure import AzureChatOpenAI
from typing import List

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
            if not all([azure_endpoint, api_key, api_version]):
                raise ValueError("Azure OpenAI environment variables (ENDPOINT, API_KEY, API_VERSION) not fully set.")
            return AzureChatOpenAI(
                deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4o"), # Default or specify deployment
                azure_endpoint=azure_endpoint,
                openai_api_key=api_key,
                api_version=api_version,
                temperature=temperature,
                timeout=timeout)
        else:
            ollama_model = os.environ.get("OLLAMA_MODEL_NAME")
            if not ollama_model:
                 raise ValueError("OLLAMA_MODEL_NAME environment variable not set for Ollama.")
            # Note: Ollama temperature might behave differently. Test for optimal results.
            return OllamaLLM(model=ollama_model, temperature=temperature, timeout=timeout)
    except Exception as e:
        e.add_note(f"Error getting LLM model: {e}")
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

        # Ensure the chain is properly constructed: prompt -> llm -> parser
        chain = prompt | llm | parser

        return chain
    except Exception as e:
        e.add_note(f"Error creating LLM prompt chain: {e}")
        raise


def feedback_classifier_generic():
    # Updated prompt with few-shot examples and refined instructions
    template = """
    Tu és um assistente de IA altamente preciso, especializado em análise e classificação de feedback de clientes em Português de Portugal. A tua tarefa é processar os feedbacks fornecidos e extrair informações específicas estritamente no formato JSON solicitado. Responde exclusivamente em Português de Portugal.

    **Objetivo:** Para cada feedback, analisa o conteúdo e preenche a seguinte estrutura JSON:

    ```json
    {{
    "classification": "...", // Classificação *exata* retirada da lista abaixo. NÃO inventar ou modificar.
    "sentiment": "...",      // Sentimento expresso ('Neutral', 'Negative', 'Very Negative').
    "feedback_summary": "..." // Resumo conciso do feedback em Português de Portugal.
    }}
    ```

    **Instruções Detalhadas e Rigorosas:**
    1.  **Leitura:** Lê atentamente cada feedback individualmente.
    2.  **Análise e Preenchimento JSON:**
        * **sentiment:** Determina o sentimento geral. Escolhe OBRIGATORIAMENTE um dos seguintes: 'Neutral', 'Negative', 'Very Negative'.
        * **feedback_summary:** Cria um resumo muito conciso do ponto principal e sugestões dos clientes. Em Português de Portugal.
        * **classification:** Esta é a parte mais crítica. Segue estas regras ABSOLUTAS:
            * Analisa o tema principal do feedback (refletido no teu resumo).
            * Compara esse tema com a lista de classificações fornecida abaixo (entre "----INICIO CLASSIFICAÇÕES----" e "---FIM CLASSIFICAÇÕES----").
            * Seleciona EXATAMENTE UMA classificação da lista. COPIA A LINHA COMPLETA da classificação escolhida, incluindo '>' se houver.
            * **NÃO MODIFIQUES, NÃO ABREVIEES, NÃO INVENTES, NÃO COMBINES classificações.** A classificação no JSON *tem* de corresponder *literalmente* a uma linha da lista.
            * Se vários temas estiverem presentes, foca-te no tema *principal* ou no mais *negativo*.
            * **Se tiveres dúvidas ou nenhum item da lista parecer adequado, escolhe a classificação que considerares MAIS PRÓXIMA.** Nunca deixes o campo vazio ou inventes uma categoria.

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
    "feedback_summary": "Cliente reporta falhas constantes na internet e demora na resolução do apoio técnico."
    }}
    ```

    *Exemplo 2:*
    Feedback: "Fui à loja MEO do Colombo e o atendimento foi 1 estrelas! O funcionário não foi muito simpático e não resolveu o meu problema rapidamente."
    JSON Esperado:
    ```json
    {{
    "classification": "Atendimento>Loja",
    "sentiment": "Very Negative",
    "feedback_summary": "Cliente muito insatisfeito com o atendimento na loja MEO Colombo."
    }}
    ```

    *Exemplo 3:*
    Feedback: "MEO - Burla com subscrição fraudulenta de serviço "cozinha fácil" \nA empresa "Cozinha Fácil" é fraudulenta e burla clientes da MEO (desconheço se também de outras operadoras) através de falsas subscrições. Nas faturas da MEO de Fevereiro e Março de 2025 constatei que me foram debitados mais de 18€ por uma alegada subscrição que nunca efetuei, tanto mais que só ontem, numa loja da MEO, ouvi falar pela primeira vez desta empresa ou "site". Ainda que desconheça o modus operandi destes burlões, admito que consigam estas falsas subscrições através de comandos de OK ou similares dissimulados nas suas publicidades on-line. Considerando que as várias queixas que consultei relacionadas com esta empresa "Cozinha Fácil" têm todas como lesados clientes da MEO, e considerando que todos os queixosos, e são muitos, negam ter efetuado qualquer subscrição de forma consciente ou deliberada, a vossa empresa não deixa de ter alguma responsabilidade por esta burla, quanto mais não seja por omissão do dever de monitorização e controlo de anunciantes e do dever de proteção dos clientes. Se não for ressarcido, pondero fazer queixa ao MP porque se trata de uma burla na forma qualificada (atento o caráter sistemático da burla e os elevadíssimos montantes obtidos das vítimas com esta prática) e alguém deveria investigar estes criminosos."
    JSON Esperado:
    ```json
    {{
    "classification": "Facturação e saldos>Comunicações>Suspeita de fraude",
    "sentiment": "Very Negative",
    "feedback_summary": "Cliente relata burla através de falsas subscrições do serviço "Cozinha Fácil". Pretende ressarcimento e considera fazer queixa ao MP devido à fraude sistemática."
    }}
    ```

    **Feedbacks a processar:**
    {feedbacks}

    **Instruções de Formato Adicionais (Obrigatório seguir):**
    {format_instructions}
    """
    # Ensure the Pydantic object matches the expected JSON structure list
    return llm_prompt_chain(ListFeedbackClassification, template, ["feedbacks", "classifications"])


def process_feedback_generic(chain, feedback_list: ListFeedback, classifications: str, batch_size: int = 10):
    # Note: Changed classifications type hint to str as get_classifications_as_string returns a string
    processed_feedback = []
    total_feedbacks = len(feedback_list.list)

    for i in range(0, total_feedbacks, batch_size):
        batch = feedback_list.list[i:min(i + batch_size, total_feedbacks)]
        # Convert batch items to a simple string representation suitable for the prompt if needed,
        # or ensure the __str__ or __repr__ method of Feedback model is appropriate.
        # Assuming the model objects in 'batch' can be directly used in the prompt formatting.
        # If models are complex, you might need to format them as simple strings here.
        batch_for_prompt = "\n---\n".join([f"Feedback ID {idx+i}: {fb.feedback_full_text}" for idx, fb in enumerate(batch)])


        try:
            # Ensure classifications is passed as a single string as expected by the prompt
            outputs = chain.invoke({
                "feedbacks": batch_for_prompt, # Pass the formatted string batch
                "classifications": classifications # Pass the single classifications string
            })

            # Important: Match the LLM output structure back to your original batch items.
            # The current Pydantic parser expects a list matching the structure.
            # If the LLM returns one JSON blob containing a list, this works.
            # If the LLM returns multiple JSON objects, the parser might fail or need adjustment.
            # We need to map the 'outputs.list' back to the original 'batch' items.
            # Assuming the LLM output list corresponds positionally to the input batch.
            if len(outputs.list) == len(batch):
                 for original_feedback, classification_output in zip(batch, outputs.list):
                     # Merge original data with LLM output
                     # Create a new FeedbackClassification object or update original_feedback if mutable
                     merged_data = original_feedback.model_dump() # Get original data
                     merged_data.update(classification_output.model_dump(exclude_unset=True)) # Update with LLM classification output
                     try:
                         processed_item = FeedbackClassification(**merged_data)
                         processed_feedback.append(processed_item)
                     except Exception as validation_error:
                         print(f"Validation Error merging feedback: {validation_error}. Data: {merged_data}")
                         # Optionally handle error: skip item, add default classification, etc.
            else:
                print(f"Warning: Mismatch between batch size ({len(batch)}) and LLM output size ({len(outputs.list)}) for batch starting at index {i}.")
                # Handle mismatch: log error, skip batch, etc.


        except Exception as e:
            print(f"Error processing batch starting at index {i}: {e}")
            # Decide how to handle batch errors: skip, retry, partial save?
            # Adding a sleep might help with rate limits if that's the cause
            #sleep(1) # Simple retry delay, adjust as needed

    return ListFeedbackClassification(list=processed_feedback)