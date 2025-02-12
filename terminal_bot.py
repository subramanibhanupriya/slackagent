from slack_file_manager import handle_file_query

def main():
    # Example file name to test
    test_file_name = "documents1.json"  # Replace with an actual file name
    response = handle_file_query(test_file_name)
    print(response)

if __name__ == "__main__":
    main()
