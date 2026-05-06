import { Team } from '../../api/client';

export function TeamPodium({ teams, scores }: { teams: Team[]; scores?: Record<string, number> }) {
  if (teams.length === 0) return null;
  return (
    <section className="team-podium" aria-label="Team results">
      {teams.map((team) => (
        <article key={team.team_id}>
          <strong>{team.team_name}</strong>
          <span>{scores?.[team.team_id] ?? 0}</span>
          <small>{team.player_ids.length} players</small>
        </article>
      ))}
    </section>
  );
}
