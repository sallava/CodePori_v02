import os
import json
import logging
import time
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import pathlib
from string import Template
import re

from openai import OpenAI, OpenAIError  # Ensure you're using OpenRouter's compatible OpenAI SDK

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed logs during troubleshooting
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("mas.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve OpenRouter API key from environment variables
openai_api_key = os.getenv('OPENROUTER_API_KEY')
if not openai_api_key:
    logger.error("OPENROUTER_API_KEY environment variable is not set.")
    raise ValueError("OPENROUTER_API_KEY environment variable is not set.")
else:
    logger.info("OpenRouter API key loaded successfully.")

# Initialize the OpenAI client for OpenRouter
client = OpenAI(
    api_key=openai_api_key,
    base_url="https://openrouter.ai/api/v1"
)

# def call_openai_chat(messages, model="deepseek/deepseek-r1-distill-llama-70b", temperature=0.5, timeout=60):
def call_openai_chat(messages, model="anthropic/claude-3.5-sonnet:beta", temperature=0.5, timeout=60):
# def call_openai_chat(messages, model="deepseek/deepseek-r1-distill-llama-70b", temperature=0.5, timeout=60):
    """
    Calls the OpenRouter/OpenAI chat completion endpoint with the updated SDK.
    """
    logger.debug(f"Sending messages to OpenAI:\n{json.dumps(messages, indent=2)}")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        logger.debug(f"Raw response from OpenAI: {response}")
        return response
    except OpenAIError as e:
        logger.warning(f"OpenAI Error: {e}")
        return None


##########################################################################
# Abstract Agent + Specialized Bot Classes
##########################################################################

class Agent(ABC):
    def __init__(self, name, prompt_file):
        self.name = name
        self.prompt_file = prompt_file
        self.prompt_template = self.load_prompt(prompt_file)
        self.reset_conversation()  # Initialize conversation history

    def reset_conversation(self):
        # Start with a single system message only
        self.conversation_history = [{"role": "system", "content": ""}]

    def load_prompt(self, prompt_file):
        full_path = os.path.join('complex_projects', prompt_file)
        if not os.path.exists(full_path):
            logger.error(f"Prompt file not found: {full_path}")
            raise FileNotFoundError(f"Prompt file not found: {full_path}")

        with open(full_path, 'r') as f:
            text = f.read()
            return Template(text)

    def update_prompt(self, replacements):
        prompt = self.prompt_template.safe_substitute(replacements)
        self.conversation_history[0]['content'] = prompt

    def communicate(self, user_message=None):
        """
        Sends conversation_history to the model, returns the text or "" on error.
        """
        if user_message:
            self.conversation_history.append({"role": "user", "content": user_message})

        response = call_openai_chat(self.conversation_history)
        if not response:
            logger.error(f"[{self.name}] No response object received.")
            return ""
        if not hasattr(response, "choices") or not response.choices:
            logger.error(f"[{self.name}] No valid choices in response.")
            logger.error(f"Full response: {response}")
            return ""
        if not hasattr(response.choices[0], "message") or not response.choices[0].message:
            logger.error(f"[{self.name}] Response.choices[0].message is missing.")
            logger.error(f"Full response: {response}")
            return ""

        assistant_msg = response.choices[0].message.content
        if assistant_msg is None:
            logger.error(f"[{self.name}] assistant_msg is None.")
            logger.error(f"Full response: {response}")
            return ""

        logger.info(f"[{self.name}] Assistant message:\n{assistant_msg}\n")
        self.conversation_history.append({"role": "assistant", "content": assistant_msg})
        return assistant_msg


class ArchitectureBot(Agent):
    """
    Returns a single JSON key: "architecture_overview".
    """
    def __init__(self, prompt_file='architecture_bot.txt'):
        super().__init__('ArchitectureBot', prompt_file)

    def generate_architecture_overview(self, project_description,language):
        self.update_prompt({"PROJECT_DESCRIPTION": project_description,"PROJECT_LANGUAGE":language})
        resp_text = self.communicate()
        if not resp_text:
            logger.error("[ArchitectureBot] Empty or invalid text response.")
            return {"architecture_overview": "Error: empty or invalid."}

        logger.info(f"Raw response from ArchitectureBot:\n{resp_text}")
        try:
            data = json.loads(resp_text)
            if "architecture_overview" not in data:
                logger.error("[ArchitectureBot] Missing key 'architecture_overview'.")
                return {"architecture_overview": "Error: missing architecture_overview key."}
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError parsing ArchitectureBot response: {e}")
            return {"architecture_overview": "Error: Invalid JSON."}


class FlowStructureBot(Agent):
    """
    Returns plain-text folder structure (no JSON).
    """
    def __init__(self, prompt_file='flow_structure_bot.txt'):
        super().__init__('FlowStructureBot', prompt_file)

    def generate_flow_structure(self, project_description,language):
        self.update_prompt({"PROJECT_DESCRIPTION": project_description,"PROJECT_LANGUAGE":language})
        resp_text = self.communicate()
        if not resp_text:
            logger.error("[FlowStructureBot] empty or invalid text.")
            return ""
        logger.info(f"[FlowStructureBot] Raw response:\n{resp_text}")
        return resp_text.strip()


class DevBot(Agent):
    """
    Generates code for a single file. A new DevBot instance is recommended per file for isolation.
    """
    def __init__(self, name, prompt_file):
        super().__init__(name, prompt_file)

    def generate_file_code(self, architecture_overview, flow_structure, file_path,
                           accumulated_code_dict, project_description, language="python"):
        # Reset conversation for each file
        self.reset_conversation()

        # Summarize existing code
        summarized_code = self._summarize_accumulated_code(accumulated_code_dict)

        file_description = f"""You are generating code for this file: {file_path}.
The target language is {language.capitalize()}.

Existing code in the project so far:
{summarized_code}

Only create new code for this file (do NOT overwrite existing files):
"""

        self.update_prompt({
            "ARCHITECTURE_OVERVIEW": architecture_overview,
            "FLOW_STRUCTURE": flow_structure,
            "MODULE_DESCRIPTION": file_description,
            "ACCUMULATED_CODE": summarized_code,
            "PROJECT_DESCRIPTION": project_description,
            "LANGUAGE": language.lower()
        })

        # Single pass (1 iteration)
        logger.info(f"{self.name} generating code for: {file_path}")
        self.communicate()
        time.sleep(1)
        return self._extract_code_block(language)

    def _summarize_accumulated_code(self, accumulated_code_dict):
        summary = ""
        for file_path, code in accumulated_code_dict.items():
            summary += f"File: {file_path}\n"
            summary += f"Description: [Previously generated code]\n\n"
        return summary.strip()

    def _extract_code_block(self, language):
        """
        Extract code from the conversation history (last AI message).
        """
        code_block_identifier = f"```{language.lower()}"
        for msg in reversed(self.conversation_history):
            content = msg["content"]
            # Check for language-specific code fence
            if code_block_identifier in content:
                try:
                    code_block = content.split(code_block_identifier, 1)[1].split("```", 1)[0].strip()
                    logger.info(f"[DevBot] Extracted {language} code block.")
                    return code_block
                except IndexError:
                    pass

            # Fallback: any triple backtick code fence
            if "```" in content:
                try:
                    code_block = content.split("```", 1)[1].split("```", 1)[0].strip()
                    logger.warning("[DevBot] Created a code block.")
                    return code_block
                except IndexError:
                    pass

        logger.warning("[DevBot] No code block found.")
        return ""


class VerificationBot(Agent):
    def __init__(self, prompt_file='verification_bot.txt'):
        super().__init__('VerificationBot', prompt_file)

    def review_code(self, accumulated_code_dict, project_description, module_code, module_name):
        # Generate a summary for verification
        summarized_code = self._summarize_accumulated_code(accumulated_code_dict)

        self.update_prompt({
            "ACCUMULATED_CODE": summarized_code,
            "PROJECT_DESCRIPTION": project_description,
            "MODULE_CODE": module_code,
            "MODULE_NAME": module_name
        })
        review_text = self.communicate()
        if not review_text:
            logger.error(f"[VerificationBot] empty or invalid review response.")
            return ""
        logger.info(f"[VerificationBot] Review:\n{review_text}")
        return review_text

    def _summarize_accumulated_code(self, accumulated_code_dict):
        """
        Create a summary of accumulated code for verification.
        """
        summary = ""
        for file_path, code in accumulated_code_dict.items():
            summary += f"File: {file_path}\n"
            summary += f"Code:\n{code}\n\n"
        return summary.strip()


class FinalizerBot(Agent):
    """
    Finalizes the code after verification and returns an array of finalized codes.
    """
    def __init__(self, name, prompt_file):
        super().__init__(name, prompt_file)

    def finalize_code(self, project_description, accumulated_code_dict, reviews, language, flow_structure):
        self.reset_conversation()

        summarized_code = self._summarize_accumulated_code(accumulated_code_dict)
        combined_reviews = "\n".join(reviews)

        self.update_prompt({
            "PROJECT_DESCRIPTION": project_description,
            "ACCUMULATED_CODE": summarized_code,
            "REVIEWS": combined_reviews,
            "LANGUAGE": language.lower(),
            "FILE_FOLDER_STRUCTRE": flow_structure
        })
        final_resp = self.communicate()
        if not final_resp:
            logger.error("[FinalizerBot] Final code empty.")
            return {"final_codes": []}  # Return empty array on failure
        logger.info("[FinalizerBot] Returned final code.")

        # Parse the JSON response
        try:
            data = json.loads(final_resp)
            if "final_codes" not in data:
                logger.error("[FinalizerBot] Missing 'final_codes' key in response.")
                return {"final_codes": []}
            return data
        except json.JSONDecodeError as e:
            logger.error(f"FinalizerBot JSONDecodeError: {e}")
            logger.error(f"Response content: {final_resp}")
            return {"final_codes": []}

    def _summarize_accumulated_code(self, accumulated_code_dict):
        """
        Create a summary of accumulated code for finalization.
        """
        summary = ""
        for file_path, code in accumulated_code_dict.items():
            summary += f"File: {file_path}\n"
            summary += f"Code:\n{code}\n\n"
        return summary.strip()


##########################################################################
# State Manager
##########################################################################

class StateManager:
    def __init__(self):
        self.project_description = ""
        self.architecture = {}
        self.flow_structure = ""
        self.accumulated_code = {}  # Dictionary {file_path: code}
        self.reviews = []

    def set_project_description(self, desc):
        self.project_description = desc

    def set_architecture(self, arch_dict):
        self.architecture = arch_dict

    def set_flow_structure(self, text):
        self.flow_structure = text

    def update_code(self, file_path, code_snippet):
        self.accumulated_code[file_path] = code_snippet

    def add_review(self, review_text):
        self.reviews.append(review_text)


##########################################################################
# Helpers: parse folder structure -> subdirs & files
##########################################################################

def parse_flow_structure(flow_text):
    """
    Parses a textual folder structure with indentation into a list of file paths.
    Example flow_text input:
        weather_forecasting_app/
          - main.py
          - logs/
            - error.log
          - modules/
            - api_handler.py
            - data_parser.py
        tests/
          - test_api_handler.py

    Returns a list of file paths:
      [
        "weather_forecasting_app/main.py",
        "weather_forecasting_app/logs/error.log",
        "weather_forecasting_app/modules/api_handler.py",
        "weather_forecasting_app/modules/data_parser.py",
        "tests/test_api_handler.py"
      ]

    Assumptions:
      - A line ending with '/' is a directory.
      - A line with '.' is likely a file (naive check).
      - Each sub-level is assumed to be ~2 spaces deeper than its parent.
      - Lines might start with '-', ' ' or tabs, so we trim them.
    """

    lines = flow_text.splitlines()
    stack = []        # Directory stack
    file_paths = []   # Final list of file paths
    prev_indent = 0   # Tracks the indentation of the current directory level

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line:
            # Skip blank lines
            continue

        # Count leading spaces to figure out indentation
        indent = len(raw_line) - len(raw_line.lstrip(' '))
        # Because we assume 2 spaces = 1 indent level, adjust accordingly

        # If indentation is less than before, pop directories from stack
        while stack and indent < prev_indent:
            stack.pop()
            prev_indent -= 2

        stripped_line = line.strip(" -\t")
        if stripped_line.endswith("/"):
            # It's a directory
            dir_name = stripped_line[:-1]  # Remove trailing slash
            stack.append(dir_name)
            prev_indent = indent + 2
        else:
            # It's presumably a file
            subpath = "/".join(stack)
            if subpath:
                file_paths.append(os.path.join(subpath, stripped_line))
            else:
                file_paths.append(stripped_line)

    return file_paths


def create_directories_and_save_file(root_dir, relative_path, content, language):
    """
    Create subdirs under `root_dir` as needed, then save 'content' to `relative_path`.
    Uses the file extension from the `relative_path` without appending a language-specific extension.
    """
    # Prevent creation of unwanted files
    unwanted_files = ["readme", "test", ".env", ".gitignore"]
    base_name = os.path.basename(relative_path).lower()
    if any(unwanted in base_name for unwanted in unwanted_files):
        logger.info(f"Skipping creation of unwanted file: {relative_path}")
        return

    # Construct the full file path
    full_path = os.path.join(root_dir, relative_path)
    dir_part = os.path.dirname(full_path)
    if not os.path.exists(dir_part):
        os.makedirs(dir_part, exist_ok=True)

    # Clean the content by removing triple backticks and language identifiers
    cleaned_content = clean_code_content(content, language)

    # Save the file
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    logger.info(f"Saved file: {full_path}.")


def clean_code_content(content, language):
    """
    Removes triple backticks and language identifiers from the code content.
    """
    # Define the code block identifiers
    code_block_start = f"```{language.lower()}"
    code_block_end = "```"

    # Remove the start identifier if present
    if content.startswith(code_block_start):
        content = content[len(code_block_start):]

    # Remove the end identifier if present
    if content.endswith(code_block_end):
        content = content[:-len(code_block_end)]

    # Additionally, strip any remaining whitespace
    return content.strip()

def clean_flow_text(flow_text):
    """
    Removes triple backticks and any language identifiers from the flow_text.
    """
    # Remove code fences like ``` or ```language
    flow_text = re.sub(r"```[\w-]*", "", flow_text)
    # Remove trailing ``` if any
    flow_text = flow_text.replace("```", "")
    return flow_text.strip()

##########################################################################
# Main generator function (SSE)
##########################################################################

def generate_project_stream(project_description, language):
    """
    Generates project code by:
      1) ArchitectureBot generates architecture overview.
      2) FlowStructureBot generates folder structure.
      3) For each file:
         - DevBot generates code.
         - VerificationBot reviews code.
         - If issues, FinalizerBot finalizes code.
         - Writes finalized code to file.
      4) Provides a download link.
    """
    state = StateManager()
    state.set_project_description(project_description)

    try:
        # 1) ArchitectureBot
        arch_bot = ArchitectureBot('architecture_bot.txt')
        arch_data = arch_bot.generate_architecture_overview(project_description, language)
        if "architecture_overview" not in arch_data:
            yield json.dumps({"error": "ArchitectureBot did not return 'architecture_overview' properly."})
            return

        state.set_architecture(arch_data)
        yield json.dumps({"architecture_overview": arch_data["architecture_overview"]})
        time.sleep(1)

        # Architecture overview
        architecture_overview = arch_data["architecture_overview"]

        # 2) FlowStructureBot
        flow_bot = FlowStructureBot('flow_structure_bot.txt')
        flow_text = flow_bot.generate_flow_structure(architecture_overview, language)
        if not flow_text:
            yield json.dumps({"error": "FlowStructureBot returned empty structure."})
            return

        # Clean the flow_text to remove any triple backticks
        flow_text = clean_flow_text(flow_text)

        state.set_flow_structure(flow_text)
        yield json.dumps({"flow_structure": flow_text})
        time.sleep(1)

        # Parse files
        file_paths = parse_flow_structure(flow_text)
        if not file_paths:
            yield json.dumps({"error": "No files found in the flow structure."})
            return

        # Define the root directory consistent with Flask's download route
        root_dir = "generated_project"

        # Initialize lists to store generated codes and reviews
        generated_codes = []
        verified_reviews = []

        # Initialize a single DevBot instance
        dev_bot = DevBot("DevBot", "dev.txt")  # Ensure 'dev.txt' exists in 'complex_projects' directory

        # For each file in the flow structure
        for rel_file in file_paths:
            yield json.dumps({"current_file": rel_file})
            time.sleep(1)

            # A) DevBot => produce code
            file_code = dev_bot.generate_file_code(
                architecture_overview=architecture_overview,
                flow_structure=flow_text,
                file_path=rel_file,
                accumulated_code_dict=state.accumulated_code,
                project_description=state.project_description,
                language=language
            )
            if not file_code:
                yield json.dumps({"error": f"DevBot failed to create code for {rel_file}."})
                logger.error(f"DevBot failed to create code for {rel_file}.")
                continue

            # B) Accumulate code + yield
            state.update_code(rel_file, file_code)
            generated_codes.append({"rel_path": rel_file, "code": file_code})
            yield json.dumps({"code_file": {"filename": rel_file, "code": file_code}})
            time.sleep(1)

            # C) Verification
            ver_bot = VerificationBot('verification_bot.txt')
            review = ver_bot.review_code(
                accumulated_code_dict=state.accumulated_code,
                project_description=state.project_description,
                module_code=file_code,
                module_name=rel_file
            )
            if review:
                verified_reviews.append(review)
                state.add_review(review)
                logger.info(f"Review for {rel_file}: {review}")
                # Yielding the review
                yield json.dumps({"verification": {rel_file: review}})
            else:
                logger.error(f"VerificationBot failed to review code for {rel_file}.")
                yield json.dumps({"error": f"VerificationBot failed to review code for {rel_file}."})
            time.sleep(1)

            # D) Check if the review indicates any issues
            # Simple heuristic: if review contains keywords like 'error', 'issue', 'fix', etc.
            issue_keywords = ['error', 'issue', 'fix', 'improve', 'incorrect', 'problem', 'bug', 'refactor']
            if any(keyword in review.lower() for keyword in issue_keywords):
                yield json.dumps({"status": f"Issues detected in {rel_file}. Initiating finalization."})
                logger.info(f"Issues detected in {rel_file}. Initiating finalization.")

                # Prepare accumulated_code_dict for FinalizerBot with only the current file
                finalizer_accumulated_code = {rel_file: state.accumulated_code[rel_file]}

                # Initialize FinalizerBot
                finalizer_bot = FinalizerBot("FinalizerBot", "finalizer_bot_1.txt")

                # Call FinalizerBot for the current file
                finalizer_response = finalizer_bot.finalize_code(
                    project_description=architecture_overview,
                    accumulated_code_dict=finalizer_accumulated_code,
                    reviews=[review],
                    language=language,
                    flow_structure=flow_text
                )

                # Check if FinalizerBot returned any codes
                if not finalizer_response.get("final_codes"):
                    yield json.dumps({"error": f"FinalizerBot failed to finalize code for {rel_file}."})
                    logger.error(f"FinalizerBot failed to finalize code for {rel_file}.")
                    continue

                # Process FinalizerBot's response
                for code_entry in finalizer_response["final_codes"]:
                    final_rel_path = code_entry.get("rel_path")
                    updated_code = code_entry.get("updated_code")
                    if not final_rel_path or not updated_code:
                        logger.warning(f"Invalid code entry from FinalizerBot: {code_entry}")
                        continue

                    # Update the accumulated code with the finalized code
                    state.update_code(final_rel_path, updated_code)

                    # Write the finalized code to the respective file
                    create_directories_and_save_file(root_dir, final_rel_path, updated_code, language)
                    yield json.dumps({"finalized_code": {"filename": final_rel_path, "code": updated_code}})
                    logger.info(f"Finalized and saved {final_rel_path} to disk.")
                    time.sleep(1)
            else:
                # If no issues, write the original code to the file
                create_directories_and_save_file(root_dir, rel_file, file_code, language)
                yield json.dumps({"status": f"No issues detected in {rel_file}. Code saved successfully."})
                logger.info(f"No issues detected in {rel_file}. Code saved successfully.")
                time.sleep(1)

        # 6) Provide a download link
        # Extract the top-level project folder name
        if file_paths:
            project_name = pathlib.PurePath(file_paths[0]).parts[0]
            logger.info(f"Extracted project name: {project_name}")

            # Project download link
            download_link = f"curl -o {project_name}.zip http://127.0.0.1:5000/download_project/{project_name}"
            yield json.dumps({"final_output": download_link})
        else:
            yield json.dumps({"error": "No files were processed."})

    except Exception as e:
        logger.error(f"Unexpected error in generate_project_stream: {e}")
        yield json.dumps({"error": str(e)})