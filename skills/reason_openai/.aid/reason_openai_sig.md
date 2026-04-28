# reason_openai — SIGNATURE TOC

## PACK INFO

Target: P:\packages\cc-skills-meta\skills\reason_openai

Files: 9

## DIRECTORY INDEX

## SIGNATURE TOC

### hooks\reason_openai_analyze.py

- **load_entries**
  (path)
- **text_len**
  (value)
- **yes_no**
  (value)
- **summarize**
  (entries)
- **main**
### hooks\reason_openai_log.py

- **extract_section**
  (text,heading)
- **infer_mode**
  (route_text)
- **infer_depth**
  (route_text)
- **make_entry**
  (content)
- **main**
### hooks\reason_openai_pending_queue.py

- **load_last_log**
- **is_already_pending**
  (entry_id)
- **main**
### hooks\reason_openai_preflight.py

- **main**
### hooks\reason_openai_quality_gate.py

- **has_heading**
  (text,heading)
- **main**
### hooks\reason_openai_review_entry.py

- **load_jsonl**
  (path)
- **save_jsonl**
  (path,rows)
- **parse_bool**
  (value)
- **main**
### hooks\reason_openai_session_reminder.py

- **load_pending**
- **main**
### hooks\reason_openai_subagent_stop.py

- **detect_agent**
  (content)
- **check_sections**
  (content,sections)
- **main**
### reason_openai_router.py

- **Mode**

## FILE INDEX

- hooks\reason_openai_analyze.py
- hooks\reason_openai_log.py
- hooks\reason_openai_pending_queue.py
- hooks\reason_openai_preflight.py
- hooks\reason_openai_quality_gate.py
- hooks\reason_openai_review_entry.py
- hooks\reason_openai_session_reminder.py
- hooks\reason_openai_subagent_stop.py
- reason_openai_router.py