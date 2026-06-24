"""
GenAI Module — Generative AI for MLB Analytics
Uses Google Gemini API (or compatible OpenAI-style API) to generate
natural language analysis for players and games.
Falls back to a structured rule-based generator when no API key is configured.
"""

import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GENAI_PROVIDER = os.getenv("GENAI_PROVIDER", "gemini")  # "gemini" or "openai"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


# ──────────────────────────────────────────────
# LLM Client — Google Gemini
# ──────────────────────────────────────────────
def _call_gemini(prompt: str) -> Optional[str]:
    """Call Google Gemini API to generate text."""
    if not GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    except ImportError:
        logger.warning("google-generativeai package not installed. "
                       "Install with: pip install google-generativeai")
        return None
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None


# ──────────────────────────────────────────────
# LLM Client — OpenAI Compatible
# ──────────────────────────────────────────────
def _call_openai(prompt: str) -> Optional[str]:
    """Call OpenAI-compatible API to generate text."""
    if not OPENAI_API_KEY:
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一位專業的 MLB 棒球數據分析師，擅長用繁體中文提供深入且易懂的球員與比賽分析。回答時請包含數據引用，並給出具體的見解。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except ImportError:
        logger.warning("openai package not installed.")
        return None
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


def call_llm(prompt: str) -> Optional[str]:
    """Call the configured LLM provider."""
    if GENAI_PROVIDER == "openai" and OPENAI_API_KEY:
        return _call_openai(prompt)
    elif GEMINI_API_KEY:
        return _call_gemini(prompt)
    elif OPENAI_API_KEY:
        return _call_openai(prompt)
    return None


# ──────────────────────────────────────────────
# Structured Rule-Based Fallback Generator
# ──────────────────────────────────────────────

def _batting_tier(avg: float) -> str:
    if avg >= 0.300: return "頂尖打者"
    if avg >= 0.270: return "優秀打者"
    if avg >= 0.250: return "合格打者"
    if avg >= 0.220: return "低於平均"
    return "掙扎中"

def _era_tier(era: float) -> str:
    if era <= 2.50: return "王牌級投手"
    if era <= 3.20: return "一線先發"
    if era <= 3.80: return "穩定先發"
    if era <= 4.50: return "中規中矩"
    return "表現不穩"

def _ops_analysis(ops: float) -> str:
    if ops >= 0.900: return "具有頂級攻擊火力"
    if ops >= 0.800: return "攻擊能力優秀"
    if ops >= 0.700: return "攻擊力中等"
    return "攻擊力偏弱"

def _luck_analysis(actual: float, expected: float, stat_name: str) -> str:
    diff = actual - expected
    if abs(diff) < 0.015:
        return f"他的{stat_name}表現與預期數據高度吻合，代表成績真實反映了實力。"
    elif diff > 0:
        return f"他的實際{stat_name}高於預期值 {diff:+.3f}，可能存在部分運氣成分，未來有回歸風險。"
    else:
        return f"他的實際{stat_name}低於預期值 {diff:+.3f}，代表運氣不佳，未來表現有望提升。"


def generate_player_analysis_fallback(player: Dict, batting: Optional[Dict],
                                       pitching: Optional[Dict],
                                       savant: Optional[Dict]) -> str:
    """Generate structured analysis without LLM."""
    name = player.get("full_name", "Unknown")
    pos = player.get("primary_position", "")
    team = player.get("team_name", "")
    is_pitcher = pos in ("P", "SP", "RP", "LHP", "RHP")

    lines = [f"## 🤖 AI 球員分析報告 — {name}\n"]

    if is_pitcher and pitching:
        era = pitching.get("era", 0)
        whip = pitching.get("whip", 0)
        so = pitching.get("strikeouts", 0)
        ip = pitching.get("innings_pitched", 0)
        w = pitching.get("wins", 0)
        l = pitching.get("losses", 0)

        tier = _era_tier(era)
        k_per_9 = round(so / ip * 9, 1) if ip > 0 else 0

        lines.append(f"### 投球表現總結")
        lines.append(f"{name} 在 2024 賽季中被定位為**{tier}**級別。")
        lines.append(f"他的防禦率（ERA）為 **{era:.2f}**，WHIP 為 **{whip:.2f}**，"
                     f"在 **{ip:.1f}** 局的投球中送出了 **{so}** 次三振"
                     f"（K/9 = {k_per_9}），戰績為 **{w}W-{l}L**。")

        if k_per_9 >= 9.0:
            lines.append(f"\n📊 **三振能力突出**：K/9 達到 {k_per_9}，具備壓制性的投球風格。")
        if whip <= 1.10:
            lines.append(f"\n📊 **控球精準**：WHIP 僅 {whip:.2f}，鮮少給予免費上壘機會。")

    elif batting:
        avg = batting.get("avg", 0)
        hr = batting.get("home_runs", 0)
        rbi = batting.get("rbi", 0)
        ops = batting.get("ops", 0)
        obp = batting.get("obp", 0)
        slg = batting.get("slg", 0)
        sb = batting.get("stolen_bases", 0)
        so = batting.get("strikeouts", 0)
        bb = batting.get("walks", 0)

        tier = _batting_tier(avg)
        ops_desc = _ops_analysis(ops)

        lines.append(f"### 打擊表現總結")
        lines.append(f"{name} 在 2024 賽季中展現了**{tier}**的水準，{ops_desc}。")
        lines.append(f"他的打擊率為 **.{int(avg * 1000):03d}**，"
                     f"上壘率 **.{int(obp * 1000):03d}** / 長打率 **.{int(slg * 1000):03d}**，"
                     f"OPS 為 **.{int(ops * 1000):03d}**。")
        lines.append(f"全壘打 **{hr}** 支、打點 **{rbi}**、盜壘 **{sb}** 次。")

        if bb > 0 and so > 0:
            bb_k_ratio = round(bb / so, 2)
            lines.append(f"\n📊 **選球紀律**：保送/三振比為 {bb_k_ratio}（{bb}BB / {so}K）"
                         f"{'，具有優秀的選球眼' if bb_k_ratio >= 0.50 else '，選球有提升空間'}。")

        if hr >= 30:
            lines.append(f"\n💪 **強打能力**：{hr} 支全壘打，屬於聯盟頂級的長打好手。")

        # Savant xBA/xSLG analysis
        if savant:
            xba = savant.get("xba")
            xslg = savant.get("xslg")
            if xba and avg > 0:
                lines.append(f"\n### Statcast 進階分析")
                lines.append(_luck_analysis(avg, xba, "打擊率 (AVG vs xBA)"))
            if xslg and slg > 0:
                lines.append(_luck_analysis(slg, xslg, "長打率 (SLG vs xSLG)"))

            ev = savant.get("avg_exit_velocity")
            barrel = savant.get("barrel_rate")
            if ev:
                lines.append(f"\n擊球初速為 **{ev:.1f} mph**"
                             f"{'，屬於聯盟前段的硬接觸打者' if ev >= 90 else ''}。")
            if barrel:
                lines.append(f"出色擊球率（Barrel%）為 **{barrel:.1f}%**"
                             f"{'，代表他能頻繁打出高品質的擊球' if barrel >= 10 else ''}。")

    lines.append(f"\n---\n*此分析由 AI 模型基於 2024 賽季數據自動生成。*")
    return "\n".join(lines)


def generate_game_analysis_fallback(game: Dict, home_prob: int,
                                     away_prob: int) -> str:
    """Generate structured game analysis without LLM."""
    home = game.get("home_team_name", "Home")
    away = game.get("away_team_name", "Away")
    home_abbr = game.get("home_team_abbr", "???")
    away_abbr = game.get("away_team_abbr", "???")
    date = game.get("game_date", "")
    home_score = game.get("home_score")
    away_score = game.get("away_score")
    status = game.get("status", "")
    venue = game.get("venue", "")

    lines = [f"## 🤖 AI 比賽分析 — {away_abbr} @ {home_abbr}\n"]
    lines.append(f"📅 日期：{date} ｜ 📍 球場：{venue}\n")

    # Pre-game prediction
    favored = home if home_prob > away_prob else away
    margin = abs(home_prob - away_prob)
    confidence = "高" if margin >= 20 else "中" if margin >= 10 else "低"

    lines.append(f"### AI 賽前預測")
    lines.append(f"根據雙方近期戰績分析，AI 模型預測 **{favored}** 較有機會獲勝。")
    lines.append(f"- {home}（主場）勝率：**{home_prob}%**")
    lines.append(f"- {away}（客場）勝率：**{away_prob}%**")
    lines.append(f"- 預測信心度：**{confidence}**")

    if home_prob > 55:
        lines.append(f"\n主場優勢加上近期表現，{home} 在本場比賽佔有一定優勢。")
    elif away_prob > 55:
        lines.append(f"\n儘管在客場作戰，{away} 憑藉更強的近期戰績仍被看好。")
    else:
        lines.append(f"\n這是一場勢均力敵的比賽，雙方實力相當接近。")

    # Post-game result (if Final)
    if status == "Final" and home_score is not None and away_score is not None:
        winner = home if home_score > away_score else away
        winner_score = max(home_score, away_score)
        loser_score = min(home_score, away_score)
        predicted_winner = home if home_prob > away_prob else away
        correct = winner == predicted_winner

        lines.append(f"\n### 比賽結果")
        lines.append(f"**{winner}** 以 **{winner_score}:{loser_score}** 贏得比賽。")

        if correct:
            lines.append(f"\n✅ **AI 預測成功！** 模型正確預測了比賽結果。")
        else:
            lines.append(f"\n❌ **AI 預測失誤。** 這也體現了棒球比賽的不確定性。")

        diff = abs(home_score - away_score)
        if diff >= 5:
            lines.append(f"這是一場懸殊的比賽，{winner} 以 {diff} 分的大幅差距取得勝利。")
        elif diff == 1:
            lines.append(f"這是一場驚心動魄的一分勝負，結果直到最後才分曉。")

    lines.append(f"\n---\n*此分析由 AI 模型基於球隊近 10 場滾動數據自動生成。*")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# Public API — Main Entry Points
# ──────────────────────────────────────────────

def generate_player_analysis(player: Dict, batting: Optional[Dict] = None,
                              pitching: Optional[Dict] = None,
                              savant: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generate AI player analysis.
    Tries LLM first, falls back to rule-based generation.
    """
    source = "rule_based"
    analysis_text = None

    # Try LLM first
    llm_prompt = _build_player_prompt(player, batting, pitching, savant)
    if llm_prompt:
        llm_result = call_llm(llm_prompt)
        if llm_result:
            analysis_text = llm_result
            source = GENAI_PROVIDER if GENAI_PROVIDER in ("gemini", "openai") else "llm"

    # Fallback to rule-based
    if not analysis_text:
        analysis_text = generate_player_analysis_fallback(
            player, batting, pitching, savant
        )

    return {
        "player_name": player.get("full_name", ""),
        "analysis": analysis_text,
        "source": source,
        "model": _get_model_name(source),
    }


def generate_game_analysis(game: Dict, home_prob: int = 50,
                            away_prob: int = 50) -> Dict[str, Any]:
    """
    Generate AI game analysis.
    Tries LLM first, falls back to rule-based generation.
    """
    source = "rule_based"
    analysis_text = None

    # Try LLM
    llm_prompt = _build_game_prompt(game, home_prob, away_prob)
    if llm_prompt:
        llm_result = call_llm(llm_prompt)
        if llm_result:
            analysis_text = llm_result
            source = GENAI_PROVIDER if GENAI_PROVIDER in ("gemini", "openai") else "llm"

    if not analysis_text:
        analysis_text = generate_game_analysis_fallback(game, home_prob, away_prob)

    return {
        "game_date": game.get("game_date", ""),
        "matchup": f"{game.get('away_team_abbr', '?')} @ {game.get('home_team_abbr', '?')}",
        "analysis": analysis_text,
        "source": source,
        "model": _get_model_name(source),
    }


def _get_model_name(source: str) -> str:
    if source == "gemini": return "Google Gemini 2.0 Flash"
    if source == "openai": return "GPT-4o Mini"
    return "Rule-Based AI Generator"


def _build_player_prompt(player: Dict, batting: Optional[Dict],
                          pitching: Optional[Dict],
                          savant: Optional[Dict]) -> Optional[str]:
    """Build a detailed LLM prompt for player analysis."""
    name = player.get("full_name", "")
    pos = player.get("primary_position", "")
    team = player.get("team_name", "")

    data_parts = [f"球員：{name}，守位：{pos}，球隊：{team}"]

    if batting and batting.get("at_bats", 0) > 0:
        data_parts.append(
            f"打擊數據 — AVG: {batting['avg']:.3f}, OBP: {batting['obp']:.3f}, "
            f"SLG: {batting['slg']:.3f}, OPS: {batting['ops']:.3f}, "
            f"HR: {batting['home_runs']}, RBI: {batting['rbi']}, "
            f"H: {batting['hits']}, BB: {batting['walks']}, "
            f"SO: {batting['strikeouts']}, SB: {batting['stolen_bases']}, "
            f"PA: {batting['plate_appearances']}"
        )

    if pitching and pitching.get("innings_pitched", 0) > 0:
        data_parts.append(
            f"投球數據 — ERA: {pitching['era']:.2f}, WHIP: {pitching['whip']:.2f}, "
            f"IP: {pitching['innings_pitched']:.1f}, SO: {pitching['strikeouts']}, "
            f"W: {pitching['wins']}, L: {pitching['losses']}, "
            f"BB: {pitching['walks_allowed']}, HR: {pitching['home_runs_allowed']}"
        )

    if savant:
        savant_parts = []
        if savant.get("avg_exit_velocity"): savant_parts.append(f"Avg EV: {savant['avg_exit_velocity']:.1f} mph")
        if savant.get("barrel_rate"): savant_parts.append(f"Barrel%: {savant['barrel_rate']:.1f}%")
        if savant.get("xba"): savant_parts.append(f"xBA: {savant['xba']:.3f}")
        if savant.get("xslg"): savant_parts.append(f"xSLG: {savant['xslg']:.3f}")
        if savant.get("xwoba"): savant_parts.append(f"xwOBA: {savant['xwoba']:.3f}")
        if savant_parts:
            data_parts.append(f"Statcast 進階數據 — {', '.join(savant_parts)}")

    data_str = "\n".join(data_parts)

    return f"""請用繁體中文分析以下 MLB 球員的 2024 賽季表現：

{data_str}

請包含以下內容：
1. 整體表現評級與定位（如頂尖、優秀、合格等）
2. 打擊/投球數據的亮點與不足
3. 如有 Statcast 數據，分析預期數據（xBA/xSLG）vs 實際數據的差異，說明運氣成分
4. 一到兩句話的總結與未來展望

請使用 Markdown 格式，標題用 ###。字數控制在 200-400 字。"""


def _build_game_prompt(game: Dict, home_prob: int, away_prob: int) -> Optional[str]:
    """Build a detailed LLM prompt for game analysis."""
    home = game.get("home_team_name", "主隊")
    away = game.get("away_team_name", "客隊")
    date = game.get("game_date", "")
    venue = game.get("venue", "")
    status = game.get("status", "")
    home_score = game.get("home_score")
    away_score = game.get("away_score")

    prompt = f"""請用繁體中文分析以下 MLB 比賽：

日期：{date}
主隊：{home}（AI 預測勝率 {home_prob}%）
客隊：{away}（AI 預測勝率 {away_prob}%）
球場：{venue}
"""

    if status == "Final" and home_score is not None:
        prompt += f"最終比分：{away} {away_score} — {home} {home_score}\n"
        prompt += f"比賽狀態：已結束\n"

    prompt += """
請包含：
1. 賽前雙方態勢分析
2. AI 預測依據說明
3. 如比賽已結束，分析比賽結果與預測的準確性
4. 簡短總結

使用 Markdown 格式，字數 150-300 字。"""

    return prompt
