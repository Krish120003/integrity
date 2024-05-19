# scraper.py
# basic functions to scrabe devpost data

from bs4 import BeautifulSoup
import requests
from send2trash import send2trash
import tempfile


def get_project_gallery(base_url):
    """Fetches links to all projects from the project gallery.

    Args:
        base_url: The base URL of the website.

    Returns:
        A list of strings containing URLs to all projects on the website.
    """

    project_links = []
    desired_start_page = "project-gallery"
    page = requests.get(base_url + desired_start_page)
    current_page = page
    header_img = None

    while current_page is not None:
        soup = BeautifulSoup(page.content, "html.parser")
        if header_img is None:
            header_img = soup.select_one(".header-image img")
            if header_img:
                header_img = header_img["src"]

            else:
                header_img = "https://i.imgur.com/9iJF8LR.png"

        # Extract project links from current page
        projects = soup.find_all(
            "a", class_=["block-wrapper", "link.fade", "link-to-software"]
        )
        for project in projects:
            project_links.append(project["href"])

        # Find the link to the next page (if it exists)
        current_page = soup.find("a", rel=["next"])

        # Fetch the next page
        if current_page:
            page = requests.get(base_url + current_page["href"])

    return project_links, header_img


def get_project_details(link):
    """
    This function scrapes project details from a given website.

    Args:
        link (str): The URL of the project webpage.

    Returns:
        dict: A dictionary containing the extracted project details. Keys include:
            title (str): Project title
            description (str): Project description (short)
            full_description (str): Full project description (might include multiple sections)
            github_url (str): URL to the project's Github repository (if found)
            team_members (list): List of URLs to team members' profiles (if found)
    """

    # if link in db
    # res = project_api_client.find_project(filter={"slug": link})
    # print(res)

    # return from db

    page = requests.get(link)
    soup = BeautifulSoup(page.content, "html.parser")

    project_details = {}

    # Get title
    title = soup.find(id="app-title")
    if title:
        project_details["title"] = title.text.strip()

    # Get short description
    description = soup.find("p", class_="large")
    if description:
        project_details["description"] = description.text.strip()

    # Get full description (might include multiple sections)
    fullInformation = soup.find(id="app-details-left")
    if fullInformation:
        innerDivs = fullInformation.find_all("div")
        full_description = ""
        for div in innerDivs:
            full_description += div.get_text(" ").strip() + "\n"
        project_details["full_description"] = full_description

    # Get Github URL
    softwareURLS = fullInformation.find(
        "ul", attrs={"data-role": True}, class_="no-bullet"
    )
    if softwareURLS:
        for url in softwareURLS.find_all("a"):
            if "https://github.com" in url["href"]:
                project_details["github_url"] = url["href"]
                break  # Stop after finding the first Github URL

    # Get team members
    teamMembers = soup.find_all("li", class_="software-team-member")
    members = []
    for member in teamMembers:
        memberLink = member.find("a", class_="user-profile-link")
        if memberLink:
            members.append(memberLink["href"])
    project_details["team_members"] = members

    return project_details


def get_hacker_projects(hacker_link):
    """
    Scrapes and returns a list of projects a hacker has worked on.

    Args:
        hacker_link (str): The URL of the hacker's profile page.

    Returns:
        list: A list of links to projects the hacker has worked on.
    """

    # checking first page
    page = requests.get(hacker_link)

    soup = BeautifulSoup(page.content, "html.parser")
    projects = soup.find_all(
        "a", class_=["block-wrapper-link", "fade", "link-to-software"]
    )
    projectLinks = []
    for link in projects:
        projectLinks.append(link["href"])

    return projectLinks


import git


def get_github_details(github_url):
    """
    Checks if a Github repository is empty.

    Args:
        github_url (str): The URL of the Github repository.

    Returns:
        num_commits (int): The number of commits in the repository.
        num_contributors (int): The number of unique contributors to the repository.
        first_commit (Datetime): The date/time of the first commit to the repository.
        last_commit (Datetime): The date/time of the last commit to the repository.
    """

    try:
        name = github_url.split("/")[-1]

        repo_path = tempfile.tempdir + "/" + name
        try:
            send2trash(repo_path)  # delete if already exists
        except:
            pass

        repo = git.Repo.clone_from(github_url, repo_path)

        commits = list(repo.iter_commits())
        num_commits = len(commits)

        contributors = set()
        for commit in commits:
            contributors.add(commit.author.env_committer_email)

        num_contributors = len(contributors)

        first_commit = commits[-1].committed_datetime

        last_commit = commits[0].committed_datetime

        return num_commits, num_contributors, first_commit, last_commit

    except:
        raise Exception("Error cloning repository")
