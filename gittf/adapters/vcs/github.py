import requests
from datetime import datetime
import subprocess

class GitHubVCS:
    ACTIONS = [
        {
            "label": "Plan",
            "description": "Re-run this Plan.",
            "identifier": "plan"
        },
        {
            "label": "Apply",
            "description": "Apply this Terraform Plan",
            "identifier": "apply"

        },
        {
            "label": "Unlock",
            "description": "Unlock this plan",
            "identifier": "unlock"

        }
    ]

    def __init__(self, token, org, repo, number, branch):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        self.token = token
        self.org = org
        self.repo = repo
        self.number = number
        self.branch = branch

    def clone(self):
        current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        repo_location = f"/tmp/{current_time}"
        clone_url = f"https://x-access-token:{self.token}@github.com/{self.org}/{self.repo}"

        subprocess.run(f"git clone --depth 1 --branch {self.branch} {clone_url} {repo_location}", shell=True, check=True)
        return repo_location

    def comment(self, comment):
        resp = requests.post(
            f"https://api.github.com/repos/{self.org}/{self.repo}/issues/{self.number}/comments",
            headers=self.headers,
            json={'body': comment}

        )
        resp.raise_for_status()

    def create_status(self, name, head_sha, external_id = None):
        resp = requests.post(
            f"https://api.github.com/repos/{self.org}/{self.repo}/check-runs",
            headers=self.headers,
            json={
                "name": name,
                "head_sha": head_sha,
                "status": "in_progress",
                "started_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                external_id: external_id
            }
        )

        resp.raise_for_status()
        return resp.json()['id']

    def update_status(self, id, conclusion, summary, text):
        resp = requests.patch(
            f"https://api.github.com/repos/{self.org}/{self.repo}/check-runs/{id}",
            headers=self.headers,
            json={
                "completed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "completed",
                "conclusion": conclusion,
                "output": {
                    "title": "Plan Output",
                    "summary": text,
                    "text": ""
                }
            }
        )

        resp.raise_for_status()

        pass

    def apply_requirements_met(self, apply_requirements):
        errors = []

        if len(apply_requirements) == 0:
            return errors

        pr = None
        try:
            pr = self._get_pr_information()
        except Exception as e:
            return [str(e)]

        if 'approved' in apply_requirements:
            reviews = self._get_reviews()
            has_one_approval = any(
                [review['state'] == 'APPROVED' for review in reviews])

            if not has_one_approval:
                errors.append(
                    f"Pull Request must have one approval before applying.")

        if 'mergeable' in apply_requirements:
            if pr['mergeable'] is not True:
                errors.append(
                    f"Pull Request must be mergeable to Apply and is currently: {pr['mergeable']}")

            if pr['mergeable_state'] in ['blocked', 'dirty', 'draft', 'unknown']:
                errors.append(
                    f"Pull Request must be in a mergeable state to apply and is currently: {pr['mergeable_state']}")

        return errors

    def _get_pr_information(self):
        resp = requests.get(
            f"https://api.github.com/repos/{self.org}/{self.repo}/pulls/{self.number}",
            headers=self.headers
        )
        resp.raise_for_status()

        return resp.json()

    def _get_pr_approvals(self):
        resp = requests.get(
            f"https://api.github.com/repos/{self.org}/{self.repo}/pulls/{self.number}/reviews",
            headers=self.headers
        )
        resp.raise_for_status()

        return resp.json()

