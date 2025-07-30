# run_helpers_test.py

from helpers import get_transcripts_list

def main():
    print("Fetching recent transcripts...\n")
    
    try:
        transcripts = get_transcripts_list()
    except Exception as e:
        print(f"Error fetching transcripts: {e}")
        return

    if not transcripts:
        print("No transcripts found.")
        return

    print(f"Found {len(transcripts)} transcripts:\n")

    for idx, transcript in enumerate(transcripts):
        title = transcript.get("title", "Untitled")
        transcript_id = transcript.get("id", "No ID")
        print(f"{idx + 1}. {title} (ID: {transcript_id})")

if __name__ == "__main__":
    main()
