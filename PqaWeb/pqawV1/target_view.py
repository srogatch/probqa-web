class TargetView:
    def __init__(self, link: str, title: str, perm_id: int, probability: str, description: str, thumbnail_url: str):
        self.link = link
        self.title = title
        self.perm_id = perm_id
        self.probability = probability
        self.description = description  # Currently shown as a tooltip
        self.thumbnail_url = thumbnail_url
