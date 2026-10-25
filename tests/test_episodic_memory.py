from memory.episodic import Episode

def test_episode():
    episode = Episode(
        event="NOVA workspace initialized",
        context="First startup",
        outcome="Workspace successfully created",
        importance=5,
    )
    data = episode.to_dict()
    assert data["event"] == "NOVA workspace initialized"
    assert data["context"] == "First startup"
    assert data["outcome"] == "Workspace successfully created"
    assert data["importance"] == 5
    assert data["created_at"]