import commons
import scratchattach as sa
import random
import warnings

from threading import Thread, Event
from scratchattach.utils.exceptions import CommentPostFailure

# Ignore scratchattach's auth warning and login data warning
warnings.filterwarnings(action='ignore', category=sa.LoginDataWarning)
warnings.filterwarnings(action='ignore', category=sa.GetAuthenticationWarning)


class CommentPostWarning(UserWarning):
    """
    Warns the user that the comment failed to post from the bot
    """


class NoAdIdSet(UserWarning):
    """
    No ad ID was set
    """


class NoProjectSelected(UserWarning):
    """
    No project was selected
    """


class Bot:
    session: sa.Session
    thread: Thread | None = None
    _project_id: int = 0
    project_id_changed: bool = False
    project: sa.Project
    lead_ins: list[str] = ["my new favorite project -->", "I LOVE THIS PROJECT SO MUCH", "very cool project i found >>",
                           "samsung anims -->", "try this nice game :)"]
    ad_id: int = 0

    def __init__(self, username: str, password: str):
        self.session = sa.login(username, password)

    def advertise(self, project_id: int):
        self.ad_id = project_id

    def target(self, project_id: int):
        self.project_id = project_id

    @property
    def project_id(self):
        return self._project_id

    @project_id.setter
    def project_id(self, new):
        self.project_id_changed = True
        self._project_id = new

    def bot(self):
        self.project = self.session.connect_project(self.project_id)

        while not commons.event.is_set():
            # Check if the bot should update its target
            if self.project_id_changed:
                self.project_id_changed = False
                self.project = self.session.connect_project(self.project_id)

            # Check if the bot has a mute and if not post the message
            print("CHECKING MUTE STATUS")
            if self.session.mute_status is None:
                print("NO MUTE STATUS")
                try:
                    # Construct the advertisement
                    link = f"https://scratch.mit.edu/projects/{self.ad_id}/"
                    message = f"{random.choice(self.lead_ins)} {link} (ID: {random.randint(1, 1000)})"

                    # Post the comment
                    self.project.post_comment(message)
                    print(f"POSTED COMMENT: {message}")

                # Catch flood errors so the program doesn't stop
                except CommentPostFailure as e:
                    warnings.warn(f"Failed to post comment because: {e}", category=CommentPostWarning)

                commons.event.wait(60)
            commons.event.wait(1)

    def stop(self):
        # Check if the thread is None and if not stop the thread
        if self.thread is not None:
            commons.event.set()
            self.thread.join()
            self.thread = None
        else:
            commons.warning = "no_bot_active"

    def start(self):
        # Start the thread
        if self.project_id != 0:
            if self.ad_id != 0:
                self.thread = Thread(target=self.bot)
                self.thread.start()
            else:
                warnings.warn("No ad ID was provided", NoAdIdSet)
                commons.warning = "no_ad_id_set"
        else:
            warnings.warn("No project was selected", NoProjectSelected)
            commons.warning = "no_project_id_set"
