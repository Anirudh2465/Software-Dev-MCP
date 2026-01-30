import os
import sys
from github import Github

def list_open_prs(repo_name):
    """
    List open pull requests for a repository.
    Args:
        repo_name (str): The repository name in format 'owner/repo'.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN environment variable not set."
        
    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        prs = repo.get_pulls(state='open', sort='created', direction='desc')
        
        results = []
        print(f"Open PRs for {repo_name}:")
        for pr in prs:
            info = f"#{pr.number}: {pr.title} (by {pr.user.login})"
            results.append(info)
            print(info)
            
        if not results:
            print("No open PRs found.")
            return "No open PRs found."
            
        md_output = [f"### 🐙 Open PRs for `{repo_name}`", "", "| # | Title | Author |", "| :--- | :--- | :--- |"]
        for pr in prs:
             md_output.append(f"| #{pr.number} | {pr.title} | {pr.user.login} |")
        
        final_output = "\n".join(md_output)
        print(final_output)
        return final_output
    except Exception as e:
        print(f"Error listing PRs: {e}")
        return f"Error: {e}"

def get_pr_diff(repo_name, pr_number):
    """
    Get the file changes (diff) of a pull request.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN environment variable not set."

    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(int(pr_number))
        
        files_data = []
        files_data.append(f"### 📝 Changes in PR #{pr_number} (`{repo_name}`)")
        
        for file in pr.get_files():
            files_data.append(f"\n#### 📄 `{file.filename}` ({file.status})\n")
            files_data.append(f"```diff\n{file.patch}\n```")
            
        output = "\n".join(files_data)
        print(output)
        return output
    except Exception as e:
        print(f"Error getting diff: {e}")
        return f"Error: {e}"

def review_pr(repo_name, pr_number, comment):
    """
    Post a review comment on a PR.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN environment variable not set."

    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(int(pr_number))
        
        pr.create_issue_comment(comment)
        print(f"Comment posted on PR #{pr_number}.")
        return "Comment posted successfully."
    except Exception as e:
        print(f"Error posting review: {e}")
        return f"Error: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python github_tools.py <command> <repo_name> [args...]")
        print("Commands: list_prs, get_diff, review")
    else:
        cmd = sys.argv[1]
        repo = sys.argv[2]
        
        if cmd == "list_prs":
            list_open_prs(repo)
        elif cmd == "get_diff" and len(sys.argv) > 3:
            get_pr_diff(repo, sys.argv[3])
        elif cmd == "review" and len(sys.argv) > 4:
            comment = " ".join(sys.argv[4:])
            review_pr(repo, sys.argv[3], comment)
        else:
            print("Invalid arguments.")
