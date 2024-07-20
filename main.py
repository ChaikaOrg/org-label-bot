from github import PullRequestReview
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


def initLabelMapping(org, rules):
    print("Rules:")
    result = []
    for team_name, label in rules:
        print(f"\tteam_name: {team_name}, label: {label}")
        team = org.get_team_by_slug(team_name)
        team_members = list(team.get_members())
        result.append(LabelMapping(team_name, label, team_members))
    return result


def is_reviewer_waiting(reviews: list[PullRequestReview]):
    approved_index = -1
    changes_requested_index = -1
    length = len(reviews)
    for i, review in enumerate(reversed(reviews)):
        if review.state == "APPROVED":
            approved_index = approved_index if approved_index != -1 else length - 1 - i
        if review.state == "CHANGES_REQUESTED":
            changes_requested_index = changes_requested_index if changes_requested_index != -1 else length - 1 - i
    return approved_index < changes_requested_index


def processLabelMapping(label_mapping: LabelMapping, pull_request):
    pr_labels = list(pull_request.get_labels())
    print(f"Current PR labels: {pr_labels}")

    # If there is at least one requisition for a review from a team -> remove the tag of this team
    requesters, team = pull_request.get_review_requests()
    print(f"requesters review requests: {list(requesters)}")
    print(f"team review requests (NOT USING): {list(team)}")
    for requester in requesters:
        if requester in label_mapping.team_members:
            for label in pr_labels:
                if label.name == label_mapping.label_name:
                    pull_request.remove_from_labels(label_mapping.label_name)
                    return

    # If there are no requests for a review, but there is no any review -> do nothing
    reviews = list(pull_request.get_reviews())
    print(f"Reviews list: {reviews}")
    if not reviews:
        return  # no reviews

    # If among those who made at least one review, the last review is not APPROVED -> do not put a label
    approve = True
    # Grouping reviews by author
    reviews_by_author = defaultdict(list)
    for rev in reviews:
        if rev.user in label_mapping.team_members:
            reviews_by_author[rev.user.login].append(rev)
    # For each author in reviews activity
    for author, value in reviews_by_author.items():
        print(f"Reviews from: {author}")
        if is_reviewer_waiting(value):
            approve = False
            print("\t reject")
        else:
            print("\t approve")
    print(f"Final PR approve: {approve}")
    if approve:
        pull_request.add_to_labels(label_mapping.label_name)
    else:
        for label in pr_labels:
            if label.name == label_mapping.label_name:
                pull_request.remove_from_labels(label_mapping.label_name)


if __name__ == '__main__':
    github_event_path = get_from_env("GITHUB_EVENT_PATH")
    with open(github_event_path, 'r') as github_event_file:
        github_event = json.load(github_event_file)

    print(f"Organization: {github_event['organization']['login']}")
    print(f"Repository: {github_event['repository']['name']}")
    print(f"PullRequest #: {github_event['pull_request']['number']}")

    auth = Auth.Token(get_from_env("GITHUB_TOKEN"))

    with Github(auth=auth) as gh:
        github_org = gh.get_organization(github_event['organization']['login'])
        repo = github_org.get_repo(github_event['repository']['name'])

        # Getting the members of all the specified groups
        label_rules = json.loads(get_from_env("RULES"))
        labelMapping = initLabelMapping(github_org, label_rules)
        print(f"labelMapping: {labelMapping}")

        pull_request = repo.get_pull(github_event['pull_request']['number'])
        for label in labelMapping:
            processLabelMapping(label, pull_request)
