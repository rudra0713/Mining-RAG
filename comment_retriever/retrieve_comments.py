import json
import locale
from comment_retriever.util import get_date_difference, process_comments


def getpreferredencoding(do_setlocale=True):
    return 'UTF-8'


locale.getpreferredencoding = getpreferredencoding


def start_processing(round_value_f, round_exist_value_f, team_value_f, team_bool_value_f, config_name):
    csv_file = '../Mining-RAG/config_json_data/merged_comments_cleaned_dates.csv'  # Replace with actual file path

    # Get round 1 comments for each project
    project_comments, project_time = process_comments(csv_file, round_value_f, round_exist_value_f, team_value_f,
                                                      team_bool_value_f)

    return [(project, comment) for project, comments in project_comments.items() for comment in comments]


def return_comments(config_name, representative=False, number_of_representative_sentences=5):
    # check_config: "config_4"
    all_comments = []

    if representative:
        json_file = f'config_json_data/representative_sentences_{config_name}.json'
        with open(json_file, 'r') as f:
            representative_sentences = json.load(f)
            for ob in representative_sentences:
                all_topics = ob['topics']
                for topic in all_topics:
                    for comment in topic['representative sentences'][:number_of_representative_sentences]:
                        all_comments.append((ob['company name'], comment))

    else:
        with open('../Mining-RAG/config_json_data/config.json', 'r') as f:
            config_f = json.load(f)
            config = config_f[config_name]
            round_value = config['round_value']
            round_exist_value = config['round_exist_value']
            team_value = config['team_value']
            team_bool_value = config['team_bool_value'].lower() == "true"
            # Process and get results for this configuration
            all_comments = start_processing(round_value, round_exist_value, team_value, team_bool_value, f"{config_name}")
                # Write to a specific sheet
    return all_comments
