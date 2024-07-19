from github import Github
from github import Auth
from collections import defaultdict
import json
import os
from dataclasses import dataclass


@dataclass
class LabelMapping:
    team_name: str
    label_name: str
    team_members: list


def get_from_env(var_name):
    value = os.environ.get(var_name)
    if value is None:
        raise Exception(f'{var_name} is not set in the environment!')
    return value


def initLabelMapping(org):
    result = []
    rules = get_from_env("RULES")
    if rules is None:
        raise Exception('Rules is not set in the environment!')
    rules_pairs = json.loads(rules)
    for team_name, label in rules_pairs:
        team = org.get_team_by_slug(team_name)
        team_members = list(team.get_members())
        result.append(LabelMapping(team_name, label, team_members))
    return result


def processLabelMapping(label_mapping: LabelMapping, pull_request):
    pr_labels = list(pull_request.get_labels())
    print(f"Labels: {pr_labels}")

    # If there is at least one requisition for a review from a team -> remove the tag of this team
    requesters, team = pull_request.get_review_requests()
    for requester in requesters:
        print(f"requester: {requester}")
        if requester in label_mapping.team_members:
            for label in pr_labels:
                if label.name == label_mapping.label_name:
                    pull_request.remove_from_labels(label_mapping.label_name)
                    return

    # If there are no requests for a review, but there is no any review -> do nothing
    reviews = list(pull_request.get_reviews())
    print(f"Reviews: {reviews}")
    if not reviews:
        return  # no reviews

    # If among those who made at least one review, the last review is not APPROVED -> do not put a label
    approve = True
    reviews_by_author = defaultdict(list)
    for rev in reviews:
        if rev.user in label_mapping.team_members:
            reviews_by_author[rev.user.login].append(rev)
    for value in reviews_by_author.values():
        if value[-1].state != "APPROVED":
            approve = False
    print(f"approve: {approve}")
    if approve:
        pull_request.add_to_labels(label_mapping.label_name)


if __name__ == '__main__':
    github_event_path = get_from_env("GITHUB_EVENT_PATH")
    with open(github_event_path, 'r') as file:
        print(file.readlines())
    exit(0)
    auth = Auth.Token(get_from_env("GITHUB_TOKEN"))

    with Github(auth=auth) as gh:
        github_org = gh.get_organization(get_from_env("GITHUB_ORG"))
        labelMapping = initLabelMapping(github_org)
        print(labelMapping)

        repo = github_org.get_repo(get_from_env("GITHUB_REPO"))

        for pr in repo.get_pulls(state="open"):
            for label in labelMapping:
                processLabelMapping(label, pr)
