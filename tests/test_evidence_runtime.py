from core.brain import BrainDecision
from core.runtime import RuntimeState
from database.schema import initialize_database
from memory.working import WorkingMemory


def test_runtime_persists_extracted_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr('database.connection.DATABASE_PATH', tmp_path / 'test.db')
    initialize_database()
    runtime = RuntimeState()
    memory = WorkingMemory(current_goal='software income')
    decision = BrainDecision(
        thought='Inspect source', goal='software income', plan=['Inspect'],
        action='http_get', reason='Inspect source',
        action_input={'url':'https://example.com/saas'},
    )
    result = '[BEGIN UNTRUSTED WEB CONTENT]<title>Simple SaaS</title>subscription free plan beginner[END UNTRUSTED WEB CONTENT]'
    runtime.extract_and_store_evidence(memory, decision, result)
    assert len(memory.opportunity_evidence) == 1
    assert memory.opportunity_evidence[0]['url'] == 'https://example.com/saas'
    assert memory.opportunity_evidence[0]['monetization'] in {'subscription','saas'}
