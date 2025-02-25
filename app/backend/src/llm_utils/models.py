import os
from time import sleep
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from src.conn_utils.mongo_conn import FeedbackClassificationPortalDaQuiexa, ListFeedbackPortalDaQuiexa, CollectionPortalDaQuixa, ListCollectionPortalDaQuixa, RelatorioMensal
from src.utils.utils_portal_da_queixa import prep_feedback_portal_da_queixa

def get_llm_model():
    use_cloud_llm = int(os.environ.get("USE_CLOUD_LLM"))
    temperature = float(os.environ.get("ARG_TEMPERASTURE"))
    timeout = int(os.environ.get("ARG_TIMEOUT"))

    try:
        if use_cloud_llm:
            return ChatGoogleGenerativeAI(model=os.environ.get("GEMINI_MODEL_NAME"), google_api_key=os.environ.get("GOOGLE_API_KEY"), temperature=temperature, timeout=timeout)
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


def feedback_classifier_portal_da_queixa():

    template = """
    Tu és um assistente especializado em análise e classificação de feedback de clientes. A tua tarefa é ler atentamente o feedback fornecido e classificá-lo de acordo com os seguintes critérios. Seja preciso e objetivo, baseando-se *exclusivamente* no texto do feedback. Sua classificação ajudará a empresa a entender melhor as necessidades e preocupações dos clientes.
    A empresa é uma operadora de TV, Net e Telefone.

    **Instruções:**

    1.  **Leia o feedback do cliente:** O feedback será fornecido a seguir ao campo "Feedback:".

    2.  **Classifique o feedback:** Preencha os seguintes campos em formato JSON: Responde em Português de Portugal.

        ```json
        {{
        "area_de_feedback": "...",
        "classificacao": "...",
        "assunto": "...",
        "sentimento": "...",
        "resumo": "..."
        "urgente": ""
        }}
        ```

    3.  **Preencha os campos com base nas seguintes definições:**

        *   **Área de Feedback** A principal área ou tópico do feedback do cliente. Escolha *UM* dos seguintes valores, ou sugira um novo se nenhum se encaixar perfeitamente:
            Exemplos (mas você pode sugerir outros):
            *   "Processo de Vendas": Problemas relacionados a interações de vendas, negociações e fechamento de negócios.
            *   "Marketing e Comunicações": Feedback sobre publicidade, promoções, mensagens da marca e comunicação geral.
            *   "Suporte/Atendimento ao Cliente": Experiência em obter ajuda e resolver problemas após se tornar cliente.
            *   "Gestão de Sucesso do Cliente": Esforços proativos para garantir que os clientes alcancem os resultados desejados.
            *   "Faturamento e Pagamentos": Faturas, pagamentos, reembolsos e transações financeiras.
            *   "Renovação de Contrato": Processos de renovação de contratos de serviço existentes, e.g. contactos via telefone por parte da empresa ou do cliente
            *   "Escalonamentos/Ouvidoria": Problemas não resolvidos pelo suporte regular, exigindo intervenção de nível superior.
            *   "Experiência do Usuário (UX)": Experiência geral de interação com os produtos, serviços, site e aplicativos da empresa.
            *   "Qualidade do Produto/Serviço": Características, funcionalidade, confiabilidade e qualidade do produto/serviço principal.
            *   "Suporte Técnico": Resolução de problemas técnicos, solução de problemas e configuração/instalação do produto.
            *   "Infraestrutura de TI": Problemas de acesso ao site/aplicativo, segurança, integrações de sistemas.
            *Se não tiver certeza, sugira o valor que lhe parece mais apropriado.

        *   **Classificação** A natureza *geral* do feedback. Escolha *UMA* das seguintes opções, ou sugira uma nova se nenhuma se encaixar perfeitamente:
            Exemplos (mas você pode sugerir outros):
            *   `Reclamação`: Expressão de insatisfação, relato de um problema ou defeito.
            *   `Elogio`: Expressão de satisfação, aprovação ou reconhecimento.
            *   `Sugestão`: Ideia de melhoria, nova funcionalidade ou mudança de processo.
            *   `Dúvida`: Pergunta sobre um produto, serviço, processo ou política.
            *   `Solicitação`: Pedido específico (excluindo resolução de problemas, que é uma `Reclamação`).
            *   `Problema de Acesso`: Dificuldade em acessar o serviço, site, aplicativo, etc.
            *   `Informação Incorreta/Enganosa`: O cliente recebeu informação errada ou se sentiu enganado.
            *   `Problema de Pagamento/Cobrança`: Problemas relacionados a faturas, pagamentos, reembolsos.

        *   **Assunto:** Um nível a mais de detalhe *dentro* da `classe`. Seja *conciso* (máximo de 4 palavras). Não seja muito especifico e tente sempre generalizar. Veja contexto adicional para ver se já existe um assunto relacionado. Se o contexto adicional tiver poucos exemplos é porque ainda existem poucos casos, neste caso pode usar um dos exemplos ou sugerir um novo.
            Exemplos (mas você pode sugerir outros):
                *  "Demora na entrega"
                *   "Produto com defeito"
                *   "Cobrança indevida"
                *   "Melhoria site"
                *   "Opções pagamento"
                *  "Qualidade produto"
                *   "Como usar"
                *   "Prazos"
                * "Política de X"
                *  "Preços"
                * "Login"
                * "Senha"

        *   **Sentimento:** O tom emocional *geral* do feedback. Escolha *UM* dos seguintes valores:
            *   `Positivo`
            *   `Negativo`
            *   `Neutro`

        *   **Resumo:** Um resumo do feedback.
        *   **Urgente:** Indique se o feedback representa uma situação crítica que requer atenção *imediata*.
            *    `Sim`
            *    `Não`

    4.  **Contexto Adicional (Classificações Anteriores):**

        Para ajudar na consistência, aqui estão alguns exemplos de classificações anteriores (área de feedback, classe e assunto). Use isso como guia, mas *não se limite* a esses exemplos.
        ```
        {additional_context}
        ```

    5.  **Restrições:**

        *   Responda *APENAS* com o JSON formatado. Não inclua texto adicional antes ou depois do JSON.
        *   Você é livre para sugerir novos valores para `área de feedback`, `classificação` e `assunto` que não estejam listados, se isso tornar a classificação mais precisa.

    6.  **Feedback a ser classificado:**

    Feedback: {feedback}

    {format_instructions}

    """

    try:
        return llm_prompt_chain(FeedbackClassificationPortalDaQuiexa, template, ["feedback", "additional_context"])
    except Exception as e:
        e.add_note(f"Error classifer portal da queixa: {e}")
        raise


def feedback_report_portal_da_queixa():
    template = """
    Você é um analista de feedback de clientes especializado em identificar tendências, padrões e áreas de melhoria em serviços de telecomunicações 
    (TV, internet e telefone). Sua tarefa é analisar os dados de feedback de clientes, fornecidos em formato JSON, e gerar um relatório conciso e acionável.
    É importante referir que este feedbach é recolhido de uma rede social do consumidor que se chama portal da quiexa onde a maior parte do feedback serão reclamações.

    **Instruções:** Responde em Português de Portugal.

    1.  **Leia os Dados de Feedback:** Os dados de feedback de cada mês serão fornecidos como uma string JSON. Essa string contém um array de objetos, 
    onde cada objeto representa um mês e contém um array de feedbacks classificados. A estrutura é a seguinte:

        ```json
        {{
            "mes": "Nome do Mês",
            "ano": Ano (Número),
            "feedbacks": [
            {{
                "area_de_feedback": "Área da Reclamação (string)",
                "classificacao": "Classe do Feedback (string)",
                "assunto": "Tópico do Feedback (string)",
                "sentimeno": "Sentimento (string - Positivo, Negativo, Neutro)",
                "sumario": "Resumo do Feedback (string)",
                "urgente": "Urgência (string - Sim, Não)",
            }},
            ... // Mais feedbacks
            ]
        }}
        ```

    2.  **Analise os Dados:** no JSON de entrada, realize as seguintes análises:

        *   **Principais Temas:**
            *   **IMPORTANTE:** Considere que a classificação inicial foi feita por um LLM sem conhecimento prévio do histórico. 
                Portanto, pode haver variações nos termos usados para descrever o *mesmo* problema (ex: "site lento", "lentidão no site", "site demorado").  
                Use seu julgamento para *agregar* temas semelhantes em categorias mais amplas e representativas.  
                Não se prenda estritamente aos termos exatos; foque no significado subjacente.
            *   **AGREGAR:** Identifique as áreas, classificações e tópicos com o *maior número* de feedbacks.
            *   **Priorizar para a Gerência:** O relatório é para a alta gerência; não detalhe cada problema específico, mas sim as *grandes áreas de preocupação*.
            *   Deves fazer análises estatísticas quando necessário.
            *   O campo "summario" contém o resumo do feedback do cliente. Utilize principalmente o campo summario para identificar a area, 
               class e subject. Os outros campos são importantes para fazer análises estatísticas.


    3.  **Gere o Relatório (Saída):**  Retorne um JSON com a seguinte estrutura:

    ```json
    {{
        "mes": "Nome do Mês",
        "ano": Ano (Número),
        "resumo": "Visão geral concisa dos principais problemas, elogios e sugestões do mês (máximo 500 palavras). Principal fonte de informacao deve ser o resumo do feedback",
        "acoes_sugeridas": [
            "Ação sugerida 1 (seja específico, com foco no problema e na solução - máximo 50 palavras).",
            "Ação sugerida 2 (seja específico - máximo 50 palavras).",
            "Ação sugerida 3 (seja específico - máximo 50 palavras).",
            "Ação sugerida 4 (seja específico - máximo 50 palavras).",
            .... mais ações
        ]
    }}


    4. *Dados mensais do feedback Feedback:**
    {json_data_str}


    {format_instructions}

    """

    try:
        return llm_prompt_chain(RelatorioMensal, template, ["json_data_str"])
    except Exception as e:
        e.add_note(f"Error report portal da queixa: {e}")
        raise


def process_feedback_portal_da_queixa(chain, feedback_list: ListFeedbackPortalDaQuiexa):
    # TODO: adicionar contexto, passar resultados dos feedbacks para segunda avaliacao (novo prompt, mehorar as classificacoes)
    try:
        res = []
        for f in feedback_list.root:
            feedback = prep_feedback_portal_da_queixa(f)
            output = chain.invoke({"feedback": feedback, "additional_context": ""})
            merged_data = {**f.model_dump(), **output.model_dump()}
            res.append(CollectionPortalDaQuixa(**merged_data))
            sleep(4) # gemini quota 15 req per min
        return ListCollectionPortalDaQuixa(root=res)
    except Exception as e:
        e.add_note(f"Error processing feedback portal da queixa: {e}")
        raise


def process_report_portal_da_queixa(chain, json_data_str):
    try:
        output = chain.invoke({"json_data_str": json_data_str})
        return output
    except Exception as e:
        e.add_note(f"Error processing relatorio portal da queixa: {e}")
        raise