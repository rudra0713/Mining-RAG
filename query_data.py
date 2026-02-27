import argparse
import os

# from langchain.vectorstores.chroma import Chroma
import json
import pandas as pd
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from chromadb import PersistentClient
# from langchain.vectorstores.chroma import Chroma  # Assuming you're using langchain_community.vectorstores.chroma or similar; adjust if
from langchain_community.vectorstores import Chroma
import json
from get_embedding_function import get_embedding_function
from collections import Counter
import matplotlib.pyplot as plt


CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""


def main():
    # Create CLI.
    parser = argparse.ArgumentParser()
    # parser.add_argument("query_text", type=str, help="The query text.", default='Query comment')
    # args = parser.parse_args()
    # query_text = args.query_text
    # query_rag(query_text)
    query_rag('')


def plot_section_frequency(section_numbers, horizontal_plot, config_name, output_directory, total_number_of_comments):
    section_freq = Counter(section_numbers)
    top_section = sorted(section_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    if not top_section:
        horizontal_plot = False
    if horizontal_plot:
        if top_section:
            pages = [f"Section {p}" for p, f in top_section]
            frequencies = [f for p, f in top_section]

            # Reverse lists to have highest frequency at the top
            pages = pages[::-1]
            frequencies = frequencies[::-1]

            plt.figure(figsize=(10, 6))
            bars = plt.barh(pages, frequencies, color='skyblue', label='Reference Frequency')
            plt.xlabel('Frequency')
            plt.ylabel('Section Number')
            plt.title('Top 10 Most Referred Sections')
            plt.grid(axis='x', linestyle='--', alpha=0.7)

            # Add frequency values beside the bars
            for i, v in enumerate(frequencies):
                plt.text(v + 0.1, i, str(v), color='black', va='center')

            # Add legend
            plt.legend(loc='lower right')

            plt.savefig(f'{output_directory}/{config_name}_comments_{total_number_of_comments}_section_frequency_horizontal.png')
        else:
            print("No page data available.")
    else:
        filtered_freq = {page: freq for page, freq in section_freq.items() if freq >= 5}
        if filtered_freq:
            sorted_pages = sorted(filtered_freq.keys())
            frequencies = [filtered_freq[page] for page in sorted_pages]
            plt.figure(figsize=(10, 6))
            plt.bar(sorted_pages, frequencies, color='skyblue')
            plt.xlabel('Page Number')
            plt.ylabel('Frequency')
            plt.title('Frequency of Page Numbers (Frequency >= 5)')
            plt.xticks(sorted_pages)  # Show all page numbers on x-axis
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.savefig(f'{output_directory}/{config_name}_comments_{total_number_of_comments}_section_frequency_vertical.png')
        else:
            print("No pages with frequency of at least 5.")


def plot_similarity(scores, config_name, output_directory, total_number_of_comments):
    plt.figure(figsize=(10, 6))
    plt.hist(scores, bins=10, range=(0, 1), color='skyblue', edgecolor='black')
    plt.xlabel('Similarity Score')
    plt.ylabel('Count')
    plt.title('Histogram of Similarity Scores (0-1)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(f'{output_directory}/{config_name}_comments_{total_number_of_comments}_similarity_scores_histogram.png')
    return


def query_rag(query_text: str):
    # Prepare the DB.
    output_directory = 'output/section_splitter'
    config_name = 'config_4'
    json_file = f'config_json_data/representative_sentences_{config_name}.json'
    best_match_count = 1
    number_of_representative_sentences = 5
    os.makedirs(output_directory, exist_ok=True)
    embedding_function = get_embedding_function()
    # db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    client = PersistentClient(path=CHROMA_PATH)
    db = Chroma(
        client=client,
        collection_name="my_collection",  # Match the collection name used in your population script
        embedding_function=embedding_function
    )

    print(f"Loading JSON file: {json_file}")

    all_representative_sentences = []
    with open(json_file, 'r') as f:
        representative_sentences = json.load(f)
        for ob in representative_sentences:
            all_topics = ob['topics']
            for topic in all_topics:
                for comment in topic['representative sentences'][:number_of_representative_sentences]:
                    all_representative_sentences.append((ob['company name'], comment))
    total_number_of_comments = len(all_representative_sentences)
    comments = []
    company_names = []
    page_numbers = []
    page_contents = []
    scores = []
    section_numbers = []
    horizontal_plot = True
    for company_name, comment in all_representative_sentences:
        # Search the DB
        if comment in comments:
            continue
        results = db.similarity_search_with_score(comment, k=best_match_count)

        # Process each result
        for i, (doc, _score) in enumerate(results):
            # For first result, include comment and company name
            similarity_score = 1 - _score
            if i == 0:
                comments.append(comment)
                company_names.append(company_name)
            else:
                # For second result, keep comment and company name empty
                comments.append("")
                company_names.append("")
            scores.append(similarity_score)
            page_contents.append(doc.page_content)
            section_numbers.append(doc.metadata['section_number'])
            page_numbers.append(int(doc.metadata['page']))
    df = pd.DataFrame({
        'comment': comments,
        'company name': company_names,
        'Guidebook page number': page_numbers,
        'Guidebook section number': section_numbers,
        'Match Score': scores,
        'Guidebook page content': page_contents
    })

    # Save to Excel
    df.to_excel(f'{output_directory}/{config_name}_comments_{total_number_of_comments}.xlsx', index=False)
    plot_section_frequency(section_numbers, horizontal_plot, config_name, output_directory, total_number_of_comments)
    plot_similarity(scores, config_name, output_directory, total_number_of_comments)

        # Create DataFrame

    # context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    # prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    # prompt = prompt_template.format(context=context_text, question=query_text)
    # # print(prompt)
    #
    # model = Ollama(model="mistral")
    # response_text = model.invoke(prompt)
    #
    # sources = [doc.metadata.get("id", None) for doc, _score in results]
    # formatted_response = f"Response: {response_text}\nSources: {sources}"
    # print(formatted_response)
    # return response_text


if __name__ == "__main__":
    main()
