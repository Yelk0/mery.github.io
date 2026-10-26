const app = document.querySelector("#app");
let store = null;
let keepSearchFocus = false;
let keepScroll = false;
let lang = localStorage.getItem("plan-mery-lang") === "en" ? "en" : "es";

function t(key, vars) {
  const pack = window.I18N[lang] || window.I18N.es;
  let text = pack[key] ?? window.I18N.es[key] ?? key;
  if (vars) {
    for (const [name, value] of Object.entries(vars)) {
      text = text.replaceAll(`{${name}}`, String(value ?? ""));
    }
  }
  return text;
}

function locale() {
  return lang === "es" ? "es-ES" : "en-GB";
}

function formatNumber(value, digits = 1) {
  return value.toLocaleString(locale(), {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[character]));
}

function signed(value, digits = 1) {
  if (value === null || value === undefined) return "—";
  const body = formatNumber(Math.abs(value), digits);
  return `${value >= 0 ? "+" : "-"}${body}`;
}

function signedPercent(value, digits = 1) {
  if (value === null || value === undefined) return "—";
  return `${signed(value, digits)}%`;
}

function signedPoints(value, digits = 1) {
  if (value === null || value === undefined) return "—";
  return `${signed(value, digits)} pts`;
}

function signedDays(value) {
  if (value === null || value === undefined) return "—";
  return `${signed(value)} ${t("dayCompact")}`;
}

function burden(value) {
  if (value === null || value === undefined) return "";
  return tone(-value);
}

function amount(value, digits = 1) {
  if (value === null || value === undefined) return "—";
  return formatNumber(Math.abs(value), digits);
}

function heads(value) {
  if (value === null || value === undefined) return "—";
  if (Math.abs(value) >= 1000000) return `${formatNumber(value / 1000000, 2)} ${t("million")}`;
  return Math.round(value).toLocaleString(locale());
}

function number(value, digits = 1) {
  if (value === null || value === undefined) return "—";
  return formatNumber(value, digits);
}

function period(term) {
  return `${term.started_on} – ${term.ended_on || t("inOffice")}`;
}

function personLink(term) {
  return `#/person/${encodeURIComponent(term.slug)}`;
}

function regionLink(slug) {
  return `#/region/${encodeURIComponent(slug)}`;
}

function indexChart(series, terms) {
  const years = [];
  for (let year = store.meta.years[0]; year <= store.meta.years[1]; year += 1) years.push(year);
  const values = years.map((year) => series[String(year)]?.share ?? null);
  const known = values.filter((value) => value !== null);
  if (!known.length) return "";
  const min = Math.min(...known);
  const max = Math.max(...known);
  const pad = Math.max((max - min) * 0.35, min * 0.08, 0.05);
  const low = Math.max(0, min - pad);
  const high = max + pad;
  const width = 760;
  const height = 240;
  const left = 52;
  const right = 44;
  const top = 16;
  const bottom = 28;
  const plotW = width - left - right;
  const plotH = height - top - bottom;
  const xOf = (index) => left + (plotW * index) / (years.length - 1);
  const yOf = (value) => top + (plotH * (high - value)) / (high - low);
  const owner = {};
  for (const term of terms) {
    for (const year of term.score.years) {
      if (!year.counted || year.excess === null || year.excess === undefined) continue;
      if (!owner[year.year] || year.days > owner[year.year].days) {
        const tone = year.excess > 0 ? "ahead" : year.excess < 0 ? "behind" : "mid";
        owner[year.year] = { days: year.days, verdict: tone };
      }
    }
  }
  const bandWidth = plotW / (years.length - 1);
  const bands = years.map((year, index) => {
    const verdict = owner[year]?.verdict;
    if (!verdict) return "";
    const x = xOf(index) - bandWidth / 2;
    return `<rect class="band band-${verdict}" x="${x.toFixed(1)}" y="${top}" width="${bandWidth.toFixed(1)}" height="${plotH}"/>`;
  }).join("");
  const points = values.flatMap((value, index) => (value === null ? [] : [`${xOf(index).toFixed(1)},${yOf(value).toFixed(1)}`]));
  const labels = years.filter((year) => year % 5 === 0).map((year) => {
    const index = years.indexOf(year);
    return `<text class="axis" x="${xOf(index).toFixed(1)}" y="${height - 8}" text-anchor="middle">${year}</text>`;
  }).join("");
  const scale = `<text class="axis" x="4" y="${top + 11}">${max.toFixed(2)}%</text><text class="axis" x="4" y="${(top + plotH).toFixed(1)}">${min.toFixed(2)}%</text>`;
  return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(t("chartLabel"))}">${bands}${scale}<polyline class="series" points="${points.join(" ")}"/>${labels}</svg>`;
}

function spellYears(spell) {
  const end = spell.ended_on ? spell.ended_on.slice(0, 4) : t("now");
  return `${spell.started_on.slice(0, 4)}–${end}`;
}

function tone(value) {
  if (value === null || value === undefined) return "";
  if (value > 0) return "faster";
  if (value < 0) return "slower";
  return "similar";
}

function euBalance(value) {
  if (!hasValue(value)) return "";
  return value > 0 ? "faster" : "slower";
}

function communityBalance(value) {
  if (!hasValue(value)) return "";
  return value < 0 ? "slower" : "faster";
}

function hasValue(value) {
  return value !== null && value !== undefined;
}

function wayKey(value, up, down) {
  return value >= 0 ? up : down;
}

function scoreSentence(leader) {
  if (!hasValue(leader.result)) return t("scoreNeedsBoth");
  const real = hasValue(leader.real_gained)
    ? t(wayKey(leader.real_gained, "realUp", "realDown"), { n: amount(leader.real_gained) })
    : t("realMissingRecord");
  let debt;
  if (leader.debt_change > 0) debt = t("debtRose", { n: amount(leader.debt_change) });
  else if (leader.debt_change < 0) debt = t("debtFell", { n: amount(leader.debt_change) });
  else debt = t("debtFlat");
  return `${real} ${debt}`;
}

function movedSentence(value, up, down, missing) {
  if (!hasValue(value)) return t(missing);
  return t(wayKey(value, up, down), { n: amount(value) });
}

function pictureSentence(leader) {
  return `${movedSentence(leader.output_gained, "pricesUp", "pricesDown", "pricesMissing")} ${movedSentence(leader.public_jobs_change, "publicUp", "publicDown", "publicMissing")} ${movedSentence(leader.private_jobs_change, "privateUp", "privateDown", "privateMissing")} ${t("besideScore")}`;
}

function stateRun(slug) {
  return slug === "ceuta" || slug === "melilla";
}

function serviceMove(nameKey, value, kind) {
  const label = t(nameKey);
  if (!hasValue(value) || value === 0) return t(kind === "days" ? "serviceFlatDays" : "serviceFlatPoints", { label });
  const key = value > 0
    ? (kind === "days" ? "serviceRoseDays" : "serviceRosePoints")
    : (kind === "days" ? "serviceFellDays" : "serviceFellPoints");
  return t(key, { label, n: amount(value) });
}

function healthCell(leader) {
  const days = signedDays(leader.health_change);
  if (!leader.health_starts_on_break) return days;
  return `${days}<span class="count-flag">${esc(t("newCount"))}</span>`;
}

function breakStartSentence(spell) {
  if (!spell.health_starts_on_break) return "";
  const opened = hasValue(spell.health_break_open_days)
    ? t("breakOpened", { n: number(spell.health_break_open_days, 0) })
    : t("breakRevised");
  const before = hasValue(spell.health_old_days)
    ? t("breakBefore", { n: number(spell.health_old_days, 0) })
    : "";
  return t("breakStart", { year: store.meta.health_break_year, opened, before });
}

function effectSentence(used, perPoint) {
  const points = used / perPoint;
  if (points > 0) return t("effectOff", { n: amount(points) });
  if (points < 0) return t("effectOn", { n: amount(-points) });
  return t("effectStill");
}

function serviceScoreLine(leader, short, nameKey, kind, perPoint, format, scaleKey) {
  const used = leader[`${short}_for_score`];
  if (!hasValue(used)) return t("serviceNoFill", { label: t(nameKey) });
  const scaleText = scaleKey ? `${t(scaleKey)} ` : "";
  if (leader[`${short}_filled`]) {
    return `${t(`${short}Filled`, { value: format(used) })} ${scaleText}${effectSentence(used, perPoint)}`;
  }
  return `${serviceMove(nameKey, leader[`${short}_change`], kind)} ${scaleText}${effectSentence(used, perPoint)}`;
}

function servicesSentence(leader) {
  if (stateRun(leader.region_slug)) return t("stateBlank");
  const days = store.meta.health_days_per_point;
  return [
    serviceScoreLine(leader, "health", "healthName", "days", days, signedDays, "tenDays"),
    breakStartSentence(leader).trim(),
    serviceScoreLine(leader, "schools", "schoolsName", "points", 1, signedPoints, ""),
    serviceScoreLine(leader, "care", "careName", "points", 1, signedPoints, ""),
  ].filter(Boolean).join(" ");
}

function spellExtras(spell, regionSlug) {
  const real = hasValue(spell.real_change)
    ? t(wayKey(spell.real_change, "realUp", "realDown"), { n: amount(spell.real_change) })
    : t("realMissingSpell");
  const jobs = hasValue(spell.public_jobs_change) || hasValue(spell.private_jobs_change)
    ? t("jobsSpell", { public: signedPercent(spell.public_jobs_change), private: signedPercent(spell.private_jobs_change) })
    : t("jobsNoSpell", { year: store.meta.jobs_first_year });
  const debt = hasValue(spell.debt_change)
    ? t("debtWent", { before: number(spell.debt_before), after: number(spell.debt_after), change: signed(spell.debt_change) })
    : t("debtNoSpell");
  const services = stateRun(regionSlug)
    ? t("stateSpell")
    : [
      hasValue(spell.health_change)
        ? t("healthWent", {
          before: number(spell.health_before, 0),
          after: number(spell.health_after, 0),
          change: signedDays(spell.health_change),
          extra: breakStartSentence(spell),
        })
        : spell.health_break
          ? t("healthCross", { year: store.meta.health_break_year })
          : t("healthNoSpell", { year: store.meta.health_first_year }),
      hasValue(spell.schools_change)
        ? t("schoolsWent", {
          before: number(spell.schools_before),
          after: number(spell.schools_after),
          change: signedPoints(spell.schools_change),
        })
        : t("schoolsNoSpell"),
      hasValue(spell.care_change)
        ? t("careWent", {
          before: number(spell.care_before),
          after: number(spell.care_after),
          change: signedPoints(spell.care_change),
        })
        : t("careNoSpell", { year: store.meta.care_first_year }),
    ].join(" ");
  const result = hasValue(spell.result) ? t("spellEconomy", { n: signed(spell.result) }) : "";
  return `${real} ${jobs} ${debt} ${services}${result}`;
}

function leaderFor(slug) {
  return store.leaders.find((leader) => leader.slug === slug || leader.spells.some((spell) => spell.slug === slug));
}

function renderHome(params) {
  const verdict = params.get("verdict") || "all";
  const query = (params.get("q") || "").trim();
  const needle = query.toLowerCase();
  const minimum = store.meta.min_career_years;
  let leaders = store.leaders;
  if (verdict === "gained") leaders = leaders.filter((leader) => leader.eligible && leader.result > 0);
  else if (verdict === "lost") leaders = leaders.filter((leader) => leader.eligible && leader.result < 0);
  else if (verdict === "early") leaders = leaders.filter((leader) => leader.counted_years < minimum);
  if (needle) {
    leaders = leaders.filter((leader) =>
      leader.name.toLowerCase().includes(needle)
      || leader.region_name.toLowerCase().includes(needle)
      || leader.party.toLowerCase().includes(needle));
  }
  const ranked = leaders.filter((leader) => leader.eligible)
    .sort((a, b) => a.rank - b.rank || a.name.localeCompare(b.name, locale()));
  const early = leaders.filter((leader) => leader.counted_years < minimum)
    .sort((a, b) => a.name.localeCompare(b.name, locale()));
  const uncovered = leaders.filter((leader) => leader.counted_years >= minimum && !leader.eligible)
    .sort((a, b) => a.name.localeCompare(b.name, locale()));
  const chips = [
    ["all", "filterAll"],
    ["gained", "filterGained"],
    ["lost", "filterLost"],
    ["early", "filterEarly"],
  ].map(([code, key]) => `<button type="button" class="chip${verdict === code ? " is-on" : ""}" data-verdict="${code}">${esc(t(key))}</button>`).join("");

  const rows = ranked.map((leader) => `<tr>
    <td class="num" data-label="${esc(t("colRank"))}">${leader.rank}</td>
    <td data-label="${esc(t("colPresident"))}"><a href="${personLink(leader)}">${esc(leader.name)}</a>${leader.party ? `<span class="party">${esc(leader.party)}</span>` : ""}</td>
    <td data-label="${esc(t("colRegion"))}"><a href="${regionLink(leader.region_slug)}">${esc(leader.region_name)}</a></td>
    <td data-label="${esc(t("colOffice"))}">${leader.spells.map((spell) => `<span class="spell">${esc(spellYears(spell))}</span>`).join("")}</td>
    <td class="num" data-label="${esc(t("colYears"))}">${leader.counted_years}</td>
    <td class="num ${tone(leader.result)}" data-label="${esc(t("colScore"))}">${signed(leader.result)}</td>
    <td class="num ${tone(leader.real_gained)}" data-label="${esc(t("colReal"))}">${signedPercent(leader.real_gained)}</td>
    <td class="num ${burden(leader.debt_change)}" data-label="${esc(t("colDebt"))}">${signedPoints(leader.debt_change)}</td>
    <td class="num ${tone(leader.output_gained)}" data-label="${esc(t("colEconomy"))}">${signedPercent(leader.output_gained)}</td>
    <td class="num ${tone(leader.index_gained)}" data-label="${esc(t("colPerson"))}">${signed(leader.index_gained)}</td>
    <td class="num ${tone(leader.people_change)}" data-label="${esc(t("colPeople"))}">${signedPercent(leader.people_change)}</td>
    <td class="num ${tone(leader.public_jobs_change)}" data-label="${esc(t("colPublic").replace("<br>", " "))}">${signedPercent(leader.public_jobs_change)}</td>
    <td class="num ${tone(leader.private_jobs_change)}" data-label="${esc(t("colPrivate").replace("<br>", " "))}">${signedPercent(leader.private_jobs_change)}</td>
    <td class="num ${burden(leader.health_change)}" data-label="${esc(t("colHealth"))}">${healthCell(leader)}</td>
    <td class="num ${burden(leader.schools_change)}" data-label="${esc(t("colSchools"))}">${signedPoints(leader.schools_change)}</td>
    <td class="num ${burden(leader.care_change)}" data-label="${esc(t("colCare"))}">${signedPoints(leader.care_change)}</td>
    <td class="num" data-label="${esc(t("colWorst"))}"><span>${leader.worst_year} <span class="${tone(leader.worst_excess)}">${signed(leader.worst_excess)}</span></span></td>
  </tr>`).join("");

  const earlyList = early.map((leader) => `<li>
    <a href="${personLink(leader)}">${esc(leader.name)}</a>
    <span>${esc(t("earlyItem", { region: leader.region_name, years: t(leader.counted_years === 1 ? "oneCountedYear" : "manyCountedYears", { n: leader.counted_years }), spells: leader.spells.map(spellYears).join(", ") }))}</span>
  </li>`).join("");

  const uncoveredList = uncovered.map((leader) => `<li>
    <a href="${personLink(leader)}">${esc(leader.name)}</a>
    <span>${esc(t("uncoveredItem", { region: leader.region_name, years: t("manyCountedYears", { n: leader.counted_years }), real: signedPercent(leader.real_gained), debt: signedPoints(leader.debt_change) }))}</span>
  </li>`).join("");

  app.innerHTML = `
    <h1>${esc(t("homeTitle"))}</h1>
    <form class="filters" id="filters">
      <input type="search" name="q" value="${esc(query)}" placeholder="${esc(t("searchPlaceholder"))}" aria-label="${esc(t("searchLabel"))}">
      ${chips}
    </form>
    ${ranked.length ? `<div class="table-scroll"><table class="rank home"><thead><tr>
      <th>${esc(t("colRank"))}</th><th>${esc(t("colPresident"))}</th><th>${esc(t("colRegion"))}</th><th>${esc(t("colOffice"))}</th><th>${esc(t("colYears"))}</th><th>${esc(t("colScore"))}</th><th>${esc(t("colReal"))}</th><th>${esc(t("colDebt"))}</th><th>${esc(t("colEconomy"))}</th><th>${esc(t("colPerson"))}</th><th>${esc(t("colPeople"))}</th><th>${t("colPublic")}</th><th>${t("colPrivate")}</th><th>${esc(t("colHealth"))}</th><th>${esc(t("colSchools"))}</th><th>${esc(t("colCare"))}</th><th>${esc(t("colWorst"))}</th>
    </tr></thead><tbody>${rows}</tbody></table></div>` : ((verdict === "early" || uncovered.length || early.length) ? "" : `<p class="empty">${esc(t("emptyFilter"))}</p>`)}
    ${(uncovered.length && verdict === "all") ? `<h2>${esc(t("noDebtTitle"))}</h2><p class="note">${esc(t("noDebtNote"))}</p><ul class="short-list">${uncoveredList}</ul>` : ""}
    ${(early.length && (verdict === "all" || verdict === "early")) ? `<h2>${esc(t("earlyTitle"))}</h2><p class="note">${esc(t("earlyNote", { n: minimum }))}</p><ul class="short-list">${earlyList}</ul>` : ""}
  `;
  const filters = document.querySelector("#filters");
  filters.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    go({ verdict, q: data.get("q") });
  });
  filters.addEventListener("input", (event) => {
    if (event.target.name !== "q") return;
    keepSearchFocus = true;
    go({ verdict, q: event.target.value });
  });
  document.querySelectorAll("[data-verdict]").forEach((button) => {
    button.addEventListener("click", () => {
      const data = new FormData(document.querySelector("#filters"));
      go({ verdict: button.dataset.verdict, q: data.get("q") });
    });
  });
}

function renderRegion(slug) {
  const region = store.regions.find((item) => item.slug === slug);
  if (!region) {
    app.innerHTML = `<p class="empty">${esc(t("noRegion", { name: slug }))}</p>`;
    return;
  }
  const terms = store.terms.filter((term) => term.region_slug === slug)
    .sort((a, b) => a.started_on.localeCompare(b.started_on));
  const timeline = terms.map((term) => `<li>
    <div>
      <a href="${personLink(term)}">${esc(term.name)}</a>
      ${term.party ? `<span class="party">${esc(term.party)}</span>` : ""}
      <p class="when">${esc(period(term))}</p>
    </div>
    <div class="result">
      <strong class="${tone(term.score.result)}">${signed(term.score.result)}</strong>
      <span>${esc(t("timelineLine", {
        real: signedPercent(term.score.real_change),
        debt: signedPoints(term.score.debt_change),
        economy: signedPercent(term.score.output_change),
        person: signed(term.score.index_change),
        people: signedPercent(term.score.people_change),
        publicJobs: signedPercent(term.score.public_jobs_change),
        privateJobs: signedPercent(term.score.private_jobs_change),
        health: signedDays(term.score.health_change),
        flag: term.score.health_starts_on_break ? t("newCountInline") : "",
        schools: signedPoints(term.score.schools_change),
        care: signedPoints(term.score.care_change),
      }))}</span>
    </div>
  </li>`).join("");
  const members = region.members.length
    ? `<table class="rank members"><thead><tr><th>${esc(t("colName"))}</th><th>${esc(t("colPost"))}</th><th>${esc(t("colFrom"))}</th><th>${esc(t("colUntil"))}</th></tr></thead><tbody>${
      region.members.map((member) => `<tr>
        <td data-label="${esc(t("colName"))}">${esc(member.name)}</td>
        <td data-label="${esc(t("colPost"))}">${esc(member.office)}</td>
        <td class="num" data-label="${esc(t("colFrom"))}">${esc(member.started_on || "—")}</td>
        <td class="num" data-label="${esc(t("colUntil"))}">${esc(member.ended_on || "—")}</td>
      </tr>`).join("")
    }</tbody></table>`
    : `<p class="empty">${esc(t("cabinetEmpty", { name: region.name }))}</p>`;
  app.innerHTML = `
    <p class="kicker"><a href="#/">${esc(t("navHome"))}</a> · ${esc(region.ine_label)}</p>
    <h1>${esc(region.name)}</h1>
    <p class="deck">${esc(t("chartDeck"))}</p>
    <figure class="chart">${indexChart(region.series, terms)}</figure>
    <ol class="timeline">${timeline}</ol>
    <h2>${esc(t("cabinetTitle"))}</h2>
    <p class="note">${esc(t("cabinetNote"))}</p>
    ${members}
  `;
}

function renderPerson(slug) {
  const leader = leaderFor(slug);
  if (!leader) {
    app.innerHTML = `<p class="empty">${esc(t("noPerson"))}</p>`;
    return;
  }
  const minimum = store.meta.min_career_years;
  const spells = leader.spells.map((spell) => {
    const term = store.terms.find((item) => item.slug === spell.slug);
    return { spell, term };
  });
  const rankLine = leader.spells.length > 1
    ? t("rankMany", { rank: leader.rank, total: leader.ranked_count, years: leader.counted_years, spells: leader.spells.length })
    : t("rankOne", { rank: leader.rank, total: leader.ranked_count, years: leader.counted_years });
  const peopleLine = [
    hasValue(leader.index_gained) ? t(wayKey(leader.index_gained, "indexUp", "indexDown"), { n: amount(leader.index_gained) }) : "",
    hasValue(leader.people_change) ? t(wayKey(leader.people_change, "peopleUp", "peopleDown"), { n: amount(leader.people_change) }) : "",
    t("peopleHelp"),
  ].filter(Boolean).join(" ");
  const realRecord = hasValue(leader.real_gained)
    ? t(wayKey(leader.real_gained, "realUp", "realDown"), { n: amount(leader.real_gained) })
    : t("realMissingRecord");
  const summary = leader.eligible
    ? `<p class="deck">${esc(t("scoreIs"))} <strong class="${tone(leader.result)}">${signed(leader.result)}</strong>. ${esc(rankLine)}</p>
       <p class="note">${esc(scoreSentence(leader))}</p>
       <p class="note">${esc(peopleLine)}</p>
       <p class="note">${esc(pictureSentence(leader))}</p>
       <p class="note">${esc(servicesSentence(leader))}</p>`
    : leader.counted_years >= minimum
      ? `<p class="deck">${esc(t("noDebtDeck", { years: leader.counted_years }))}</p>
         <p class="note">${esc(pictureSentence(leader))} ${esc(realRecord)}</p>
         <p class="note">${esc(servicesSentence(leader))}</p>`
      : `<p class="deck">${esc(t("earlyDeck", { years: t(leader.counted_years === 1 ? "oneCountedYear" : "manyCountedYears", { n: leader.counted_years }), minimum }))}</p>
         ${leader.counted_years ? `<p class="note">${esc(`${scoreSentence(leader)} ${pictureSentence(leader)} ${servicesSentence(leader)}`)}</p>` : ""}`;
  const between = leader.spells.length > 1 ? `<p class="note">${esc(t("between"))}</p>` : "";
  const worst = leader.worst_year === null
    ? ""
    : `<p class="note">${esc(t("worstYear", { year: leader.worst_year, gap: signed(leader.worst_excess) }))}</p>`;
  const spellBlocks = spells.map(({ spell, term }) => {
    const moveText = hasValue(spell.output_change)
      ? t(spell.output_change >= 0 ? "spellUp" : "spellDown", {
        period: period(spell),
        n: amount(spell.output_change),
        shareBefore: number(spell.share_before, 2),
        shareAfter: number(spell.share_after, 2),
        indexBefore: number(spell.index_before),
        indexAfter: number(spell.index_after),
        indexChange: signed(spell.index_change),
        popBefore: heads(spell.population_before),
        popAfter: heads(spell.population_after),
        people: signedPercent(spell.people_change),
        extras: spellExtras(spell, leader.region_slug),
      })
      : t("spellNoYear", { period: period(spell) });
    const years = (term?.score.years || []).map((year) => `<tr>
      <td class="num" data-label="${esc(t("colYear"))}">${year.year}</td>
      <td class="num" data-label="${esc(t("colDays"))}">${year.days}</td>
      <td class="num" data-label="${esc(t("colRegion"))}">${number(year.region_growth)}%</td>
      <td class="num" data-label="${esc(t("colSpain"))}">${number(year.spain_growth)}%</td>
      <td class="num ${tone(year.excess)}" data-label="${esc(t("colDiff"))}">${signed(year.excess)}</td>
      <td data-label="${esc(t("colCounted"))}">${year.counted ? esc(t("yes")) : esc(t("no"))}</td>
    </tr>`).join("");
    const cabinet = term?.cabinet.length
      ? `<ul class="short-list">${term.cabinet.map((member) => `<li><strong>${esc(member.name)}</strong><span>${esc(member.office)} · ${esc(member.started_on)} – ${esc(member.ended_on || t("openEnded"))}</span></li>`).join("")}</ul>`
      : `<p class="empty">${esc(t("spellCabinetEmpty"))}</p>`;
    return `
      <h2>${esc(spellYears(spell))}</h2>
      <p class="note">${esc(moveText)}</p>
      <table class="rank years"><thead><tr>
        <th>${esc(t("colYear"))}</th><th>${esc(t("colDays"))}</th><th>${esc(t("colRegion"))}</th><th>${esc(t("colSpain"))}</th><th>${esc(t("colDiff"))}</th><th>${esc(t("colCounted"))}</th>
      </tr></thead><tbody>${years}</tbody></table>
      <h2>${esc(t("spellCabinet"))}</h2>
      ${cabinet}
    `;
  }).join("");
  app.innerHTML = `
    <p class="kicker"><a href="${regionLink(leader.region_slug)}">${esc(leader.region_name)}</a></p>
    <h1>${esc(leader.name)}</h1>
    <p class="when">${leader.spells.map((spell) => esc(period(spell))).join(" · ")}${leader.party ? ` · ${esc(leader.party)}` : ""}</p>
    ${summary}
    ${between}
    ${worst}
    <p class="note">${esc(t("yearRowsNote"))}</p>
    ${spellBlocks}
  `;
}

function roundHalfUp(value, digits = 1) {
  const factor = 10 ** digits;
  const sign = value < 0 ? -1 : 1;
  return sign * Math.floor(Math.abs(value) * factor + 0.5 + 1e-8) / factor;
}

function labNear(left, right) {
  return Math.abs(left - right) < 0.001;
}

function labTerm(value) {
  const shown = roundHalfUp(value, 2);
  const text = Math.abs(shown) >= 10 ? shown.toFixed(1) : shown.toFixed(2).replace(/0$/, "");
  return `${shown > 0 ? "+" : shown < 0 ? "−" : ""}${text.replace("-", "")}`;
}

const LAB_EXAMPLE = { real: 8, debt: 4, schools: 2, care: -4, health: -10 };
let heldLab = null;
let heldExample = false;
let heldLaw = null;
let laws = [];

function labWorst() {
  return {
    schools: store.meta.schools_worst,
    care: store.meta.care_worst,
    health: store.meta.health_worst,
  };
}

function economyPile() {
  const step = (label, end = false) => `<li${end ? ' class="pile-end"' : ""}>${esc(label)}</li>`;
  const sum = (name, num, den, share, stepText, people, gap, gapClass = "") => `
    <li class="sum">
      <b>${esc(name)}</b>
      <strong class="${gapClass}">${esc(gap)}</strong>
      <span class="frac">
        <span class="over"><b>${esc(num)}</b><span>${esc(den)}</span></span>
        <span class="eq">=</span>
        <span class="share">${esc(share)}</span>
      </span>
      <em>${esc(stepText)} = <span class="${gapClass}">${esc(gap)}</span></em>
      <i>${esc(people)}</i>
    </li>`;
  const year = (text, rows) => `
    <p class="worked-year">${esc(text)}</p>
    <ol class="sums">${rows}</ol>`;
  return `
    <div class="pile">
      <ol class="pile-years">
        ${step(t("pileBefore"))}
        ${step(t("pileYear"))}
        ${step(t("pileYear"))}
        ${step(t("pileYear"))}
        ${step(t("pileYear"))}
        ${step(t("pileEnd"), true)}
      </ol>
      <p>${esc(t("pileCaption", { year: store.meta.years[1] }))}</p>
      <details class="learn"${heldExample ? " open" : ""}>
        <summary>${esc(t("exMore"))}</summary>
      <div class="worked">
        <p class="worked-title">${esc(t("exTitle"))}</p>
        <p>${esc(t("exIntro"))}</p>
        <p class="formula">
          <span class="over"><b>${esc(t("exFormulaNum"))}</b><span>${esc(t("exFormulaDen"))}</span></span>
          <span class="eq">− 1</span>
        </p>
        ${year(t("exBefore"), `
          ${sum(t("exM0"), t("exStartNum"), t("exStartDen"), t("exStartShare"), t("exStartStep"), t("exStartPeople"), t("exGap0"))}
          ${sum(t("exC0"), t("exStartNum"), t("exStartDen"), t("exStartShare"), t("exStartStep"), t("exStartPeople"), t("exGap0"))}
        `)}
        ${year(t("exYear1"), `
          ${sum(t("exM0"), t("exM1num"), t("exStartDen"), t("exM1share"), t("exM1step"), t("exM1people"), t("exM1Gap"), "slower")}
          ${sum(t("exC0"), t("exC1num"), t("exStartDen"), t("exC1share"), t("exC1step"), t("exC1people"), t("exC1Gap"), "faster")}
        `)}
        ${year(t("exYear2"), `
          ${sum(t("exM0"), t("exM2num"), t("exDen2"), t("exM2share"), t("exM2step"), t("exM1people"), t("exM2Gap"), "slower")}
          ${sum(t("exC0"), t("exC2num"), t("exDen2"), t("exC2share"), t("exC2step"), t("exC2people"), t("exC2Gap"), "faster")}
        `)}
        ${year(t("exYear3"), `
          ${sum(t("exM0"), t("exM3num"), t("exDen2"), t("exM3share"), t("exM3step"), t("exM3people"), t("exM3Gap"), "slower")}
          ${sum(t("exC0"), t("exC3num"), t("exDen2"), t("exC3share"), t("exC3step"), t("exC3people"), t("exC3Gap"), "faster")}
        `)}
        ${year(t("exYear4"), `
          ${sum(t("exM0"), t("exM3num"), t("exDen4"), t("exM4share"), t("exM4step"), t("exM3people"), t("exM4Gap"), "slower")}
          ${sum(t("exC0"), t("exC4num"), t("exDen4"), t("exC4share"), t("exC4step"), t("exC4people"), t("exC4Gap"), "faster")}
        `)}
        <p>${esc(t("exFoot"))}</p>
      </div>
      </details>
    </div>`;
}

function scoreLabHtml() {
  const start = heldLab || LAB_EXAMPLE;
  const dial = (key, name, min, max, step, value, before = "", after = "") => `
    <div class="dial" data-key="${key}">
      <div class="dial-top">
        <label for="lab-${key}">${name}</label>
        <output id="lab-${key}-out" for="lab-${key}"></output>
      </div>
      ${before}
      <input id="lab-${key}" data-key="${key}" type="range" min="${min}" max="${max}" step="${step}" value="${value}" aria-valuemin="${min}" aria-valuemax="${max}">
      <p class="dial-hint" id="lab-${key}-say"></p>
      ${after}
    </div>`;
  return `
    <div class="lab" id="score-lab">
      <div class="lab-board">
        <div class="lab-sticky">
          <p class="kicker">${esc(t("labScore"))}</p>
          <p class="lab-total" id="lab-total" aria-live="polite">+9.0</p>
          <p class="lab-sum" id="lab-sum"></p>
        </div>
        <p class="lab-key">${esc(t("labKey"))}</p>
        <ol class="lab-parts">
          <li class="lab-part" data-part="real"><span>${esc(t("partEconomy"))}</span><b></b><span class="meter" aria-hidden="true"><span class="meter-neg"><i></i></span><span class="meter-zero"></span><span class="meter-pos"><i></i></span></span></li>
          <li class="lab-part" data-part="debt"><span>${esc(t("partDebt"))}</span><b></b><span class="meter" aria-hidden="true"><span class="meter-neg"><i></i></span><span class="meter-zero"></span><span class="meter-pos"><i></i></span></span></li>
          <li class="lab-part" data-part="schools"><span>${esc(t("partSchools"))}</span><b></b><span class="meter" aria-hidden="true"><span class="meter-neg"><i></i></span><span class="meter-zero"></span><span class="meter-pos"><i></i></span></span></li>
          <li class="lab-part" data-part="care"><span>${esc(t("partCare"))}</span><b></b><span class="meter" aria-hidden="true"><span class="meter-neg"><i></i></span><span class="meter-zero"></span><span class="meter-pos"><i></i></span></span></li>
          <li class="lab-part" data-part="health"><span>${esc(t("partSurgery"))}</span><b></b><span class="meter" aria-hidden="true"><span class="meter-neg"><i></i></span><span class="meter-zero"></span><span class="meter-pos"><i></i></span></span></li>
        </ol>
      </div>
      <div class="lab-controls">
        <div class="lab-presets">
          <button type="button" class="chip is-on" data-preset="example">${esc(t("presetExample"))}</button>
          <button type="button" class="chip" data-preset="missing">${esc(t("presetMissing"))}</button>
        </div>
        ${dial("real", esc(t("dialReal")), -20, 20, 0.1, start.real, economyPile())}
        ${dial("debt", esc(t("dialDebt")), -25, 25, 0.1, start.debt)}
        ${dial("schools", esc(t("dialSchools")), -12, 12, 0.1, start.schools, "", `<button type="button" class="chip" data-fill="schools">${esc(t("fillWorst"))}</button>`)}
        ${dial("care", esc(t("dialCare")), -12, 16, 0.1, start.care, `<p class="lab-alert"><strong>${esc(t("careAlertTitle"))}</strong> ${esc(t("careAlert"))}</p>`, `<button type="button" class="chip" data-fill="care">${esc(t("fillWorst"))}</button>`)}
        ${dial("health", esc(t("dialHealth")), -50, 70, 1, start.health, "", `<button type="button" class="chip" data-fill="health">${esc(t("fillWorst"))}</button>`)}
      </div>
    </div>`;
}

function readLab(lab) {
  const read = (key) => Number(lab.querySelector(`#lab-${key}`).value);
  const real = read("real");
  const debt = read("debt");
  const schools = read("schools");
  const care = read("care");
  const health = read("health");
  const days = store.meta.health_days_per_point;
  const parts = {
    real,
    debt: -store.meta.debt_weight * debt,
    schools: -schools,
    care: -care,
    health: -health / days,
  };
  const raw = parts.real + parts.debt + parts.schools + parts.care + parts.health;
  return { real, debt, schools, care, health, parts, score: roundHalfUp(raw, 1) };
}

function plainAmount(value) {
  const rounded = roundHalfUp(Math.abs(value), 2);
  const text = String(rounded);
  const fraction = text.includes(".") ? text.split(".")[1].replace(/0$/, "") : "";
  return formatNumber(rounded, fraction.length);
}

function scoreWords(points, plural = false) {
  const amountText = plainAmount(points);
  if (points > 0) return t(plural ? "addPlural" : "adds", { n: amountText });
  if (points < 0) return t(plural ? "takeOffPlural" : "takesOff", { n: amountText });
  return t(plural ? "changeNothing" : "changesNothing");
}

function labSentences(state) {
  const days = store.meta.health_days_per_point;
  const branch = (value, zero, up, down, vars) => t(value > 0 ? up : value < 0 ? down : zero, vars);
  return {
    real: branch(state.real, "labRealZero", "labRealUp", "labRealDown", { n: plainAmount(state.real) }),
    debt: branch(state.debt, "labDebtZero", "labDebtUp", "labDebtDown", { n: plainAmount(state.debt), half: plainAmount(state.parts.debt) }),
    schools: branch(state.schools, "labSchoolsZero", "labSchoolsUp", "labSchoolsDown", { n: plainAmount(state.schools) }),
    care: branch(state.care, "labCareZero", "labCareUp", "labCareDown", { n: plainAmount(state.care) }),
    health: branch(state.health, "labHealthZero", "labHealthUp", "labHealthDown", {
      n: plainAmount(state.health),
      days,
      points: plainAmount(state.parts.health),
    }),
  };
}

function paintScoreLab(lab) {
  const state = readLab(lab);
  const worst = labWorst();
  const total = lab.querySelector("#lab-total");
  total.textContent = signed(state.score);
  total.className = `lab-total ${tone(state.score)}`;
  const order = ["real", "debt", "schools", "care", "health"];
  const names = {
    real: t("partEconomy"),
    debt: t("partDebt"),
    schools: t("partSchools"),
    care: t("partCare"),
    health: t("partSurgery"),
  };
  lab.querySelector("#lab-sum").textContent = order.map((key) => `${names[key]} ${scoreWords(state.parts[key], key === "schools")}.`).join(" ");
  const scale = 12;
  for (const key of order) {
    const row = lab.querySelector(`[data-part="${key}"]`);
    const points = state.parts[key];
    const value = row.querySelector("b");
    value.textContent = scoreWords(points, key === "schools");
    value.className = tone(points);
    const width = Math.min(100, Math.abs(points) / scale * 100);
    row.querySelector(".meter").style.color = points > 0 ? "var(--ahead)" : points < 0 ? "var(--behind)" : "var(--muted)";
    row.querySelector(".meter-pos i").style.width = points > 0 ? `${width}%` : "0";
    row.querySelector(".meter-neg i").style.width = points < 0 ? `${width}%` : "0";
    row.classList.toggle("is-worst", key !== "real" && key !== "debt" && labNear(state[key], worst[key]));
  }
  const headlines = {
    real: state.real > 0 ? t("realBigger", { n: plainAmount(state.real) }) : state.real < 0 ? t("realSmaller", { n: plainAmount(state.real) }) : t("realSame"),
    debt: state.debt > 0 ? t("debtMore", { n: plainAmount(state.debt) }) : state.debt < 0 ? t("debtLess", { n: plainAmount(state.debt) }) : t("debtSame"),
    schools: state.schools > 0 ? t("gapWorse", { n: plainAmount(state.schools) }) : state.schools < 0 ? t("gapBetter", { n: plainAmount(state.schools) }) : t("gapSame"),
    care: state.care > 0 ? t("gapWorse", { n: plainAmount(state.care) }) : state.care < 0 ? t("gapBetter", { n: plainAmount(state.care) }) : t("gapSame"),
    health: state.health > 0 ? t("waitLonger", { n: plainAmount(state.health) }) : state.health < 0 ? t("waitShorter", { n: plainAmount(state.health) }) : t("waitSame"),
  };
  const sentences = labSentences(state);
  for (const key of ["real", "debt", "schools", "care", "health"]) {
    const input = lab.querySelector(`#lab-${key}`);
    const output = lab.querySelector(`#lab-${key}-out`);
    output.textContent = headlines[key];
    output.className = key === "real" ? tone(state[key]) : burden(state[key]);
    lab.querySelector(`#lab-${key}-say`).textContent = sentences[key];
    const min = Number(input.min);
    const max = Number(input.max);
    input.style.setProperty("--pct", `${(state[key] - min) / (max - min) * 100}%`);
    const fill = lab.querySelector(`[data-fill="${key}"]`);
    if (fill) fill.classList.toggle("is-on", labNear(state[key], worst[key]));
  }
  const values = { real: state.real, debt: state.debt, schools: state.schools, care: state.care, health: state.health };
  const matches = (preset) => Object.entries(preset).every(([key, value]) => labNear(values[key], value));
  lab.querySelector('[data-preset="example"]').classList.toggle("is-on", matches(LAB_EXAMPLE));
  lab.querySelector('[data-preset="missing"]').classList.toggle("is-on", matches({
    real: LAB_EXAMPLE.real,
    debt: LAB_EXAMPLE.debt,
    ...worst,
  }));
}

function setLab(lab, values) {
  for (const [key, value] of Object.entries(values)) {
    const input = lab.querySelector(`#lab-${key}`);
    input.value = String(value);
  }
  paintScoreLab(lab);
}

function bindScoreLab() {
  const lab = document.querySelector("#score-lab");
  if (!lab) return;
  lab.addEventListener("input", (event) => {
    const key = event.target.dataset.key;
    lab.querySelectorAll(".lab-part").forEach((part) => part.classList.toggle("is-hot", part.dataset.part === key));
    paintScoreLab(lab);
  });
  lab.addEventListener("click", (event) => {
    const preset = event.target.closest("[data-preset]");
    if (preset) {
      const worst = labWorst();
      setLab(lab, preset.dataset.preset === "missing"
        ? { real: LAB_EXAMPLE.real, debt: LAB_EXAMPLE.debt, schools: worst.schools, care: worst.care, health: worst.health }
        : LAB_EXAMPLE);
      return;
    }
    const fill = event.target.closest("[data-fill]");
    if (!fill) return;
    setLab(lab, { [fill.dataset.fill]: labWorst()[fill.dataset.fill] });
  });
  paintScoreLab(lab);
}

function renderMethod() {
  const minimum = store.meta.min_career_years;
  app.innerHTML = `
    <p class="kicker">${esc(t("methodKicker"))}</p>
    <h1>${esc(t("methodTitle"))}</h1>
    <p class="deck">${esc(t("methodDeck"))}</p>
    ${scoreLabHtml()}
    <p class="note">${esc(t("methodNote", { n: minimum }))}</p>
    <p class="note">${esc(t("sources"))} <a href="${esc(store.meta.volume_url)}">${esc(t("sourceReal"))}</a>, <a href="${esc(store.meta.debt_url)}">${esc(t("sourceDebt"))}</a>, <a href="${esc(store.meta.schools_url)}">${esc(t("sourceSchools"))}</a>, <a href="${esc(store.meta.care_url)}">${esc(t("sourceCare"))}</a>, <a href="${esc(store.meta.health_url)}">${esc(t("sourceHealth"))}</a>. <a href="#/data">${esc(t("dataLink"))}</a>. <a href="#/missing">${esc(t("sourceMissing"))}</a>.</p>
  `;
  bindScoreLab();
}

function renderData() {
  const meta = store.meta;
  const from = meta.years[0];
  const to = meta.years[1];
  const link = (href, label, outside = true) => `<a href="${esc(href)}"${outside ? ' target="_blank" rel="noopener"' : ""}>${esc(label)}</a>`;
  const row = (name, body, links, inScore) => `
    <li>
      <div>
        <strong>${esc(name)}</strong>
        <span>${esc(body)}</span>
        <p class="source-links">${links}</p>
      </div>
      <b class="${inScore ? "faster" : ""}">${esc(t(inScore ? "dataInBadge" : "dataOutBadge"))}</b>
    </li>`;
  app.innerHTML = `
    <p class="kicker">${esc(t("dataKicker"))}</p>
    <h1>${esc(t("dataTitle"))}</h1>
    <p class="deck">${esc(t("dataDeck"))}</p>
    <h2>${esc(t("dataInTitle"))}</h2>
    <p class="note">${esc(t("dataInDeck"))}</p>
    <ul class="compare sources">
      ${row(t("dataRealTitle"), t("dataReal", { title: meta.volume_title, from, to }), link(meta.volume_url, t("dataOpen")), true)}
      ${row(t("dataDebtTitle"), t("dataDebt", { title: meta.debt_title, from, to }), `${link(meta.debt_url, t("dataOpen"))}${link(meta.debt_file, t("dataCsv"))}`, true)}
      ${row(t("dataSchoolsTitle"), t("dataSchools", { title: meta.schools_title, from: meta.schools_first_year, to }), link(meta.schools_url, t("dataOpen")), true)}
      ${row(t("dataCareTitle"), t("dataCare", { title: meta.care_title, from: meta.care_first_year, to }), link(meta.care_url, t("dataOpen")), true)}
      ${row(t("dataHealthTitle"), t("dataHealth", { title: meta.health_title, from: meta.health_first_year, to }), `${link(meta.health_url, t("dataOpen"))}${link("#/missing", t("dataBreak"), false)}`, true)}
    </ul>
    <h2>${esc(t("dataBesideTitle"))}</h2>
    <p class="note">${esc(t("dataBesideDeck"))}</p>
    <ul class="compare sources">
      ${row(t("dataGdpTitle"), t("dataGdp", { table: meta.gdp_table, title: meta.gdp_title, from, to }), link(meta.gdp_url, t("dataOpen")), false)}
      ${row(t("dataPersonTitle"), t("dataPerson", { table: meta.per_capita_table, title: meta.per_capita_title, from, to }), link(meta.per_capita_url, t("dataOpen")), false)}
      ${row(t("dataPopTitle"), t("dataPop"), `${link(meta.gdp_url, `${t("dataTable")} ${meta.gdp_table}`)}${link(meta.per_capita_url, `${t("dataTable")} ${meta.per_capita_table}`)}`, false)}
      ${row(t("dataJobsTitle"), t("dataJobs", { table: meta.jobs_table, title: meta.jobs_title, from: meta.jobs_first_year }), link(meta.jobs_url, t("dataOpen")), false)}
      ${row(t("dataBalanceTitle"), t("dataBalance", { title: meta.balance_title, from, to }), link(meta.balance_url, t("dataOpen")), false)}
      ${row(t("dataSpainTitle"), t("dataSpain", { title: meta.spain_title, from, to }), link(meta.spain_url, t("dataOpen")), false)}
      ${row(t("dataCentralTitle"), t("dataCentral", { title: meta.central_title, from: meta.central_from, to: meta.central_to }), link(meta.central_url, t("dataOpen")), false)}
      ${row(t("dataSpainDebtTitle"), t("dataSpainDebt", { title: meta.spain_debt_title }), `${link(meta.spain_debt_url, t("dataOpen"))}${link(meta.spain_debt_file, t("dataCsv"))}`, false)}
      ${row(t("dataEuTitle"), t("dataEu", { title: meta.eu_title }), link(meta.eu_url, t("dataOpen")), false)}
      ${row(t("dataEuVolumeTitle"), t("dataEuVolume", { title: meta.eu_volume_title, from: meta.eu_volume_from, to: meta.eu_volume_to }), link(meta.eu_volume_url, t("dataOpen")), false)}
      ${row(t("dataBudgetTitle"), t("dataBudget", { title: meta.budget_title, to }), link(meta.budget_url, t("dataOpen")), false)}
      ${row(t("dataStateBudgetTitle"), t("dataStateBudget", { title: meta.state_budget_title, from: meta.state_budget_from, to: meta.state_budget_to }), link(meta.state_budget_url, t("dataOpen")), false)}
      ${row(t("dataFlowTitle"), t("dataFlow", { title: meta.flow_title, to: meta.flow_last_year }), link(meta.flow_url, t("dataOpen")), false)}
    </ul>
    <h2>${esc(t("dataPeopleTitle"))}</h2>
    <p class="note">${esc(t("dataPeopleDeck"))}</p>
    <ul class="compare sources">
      <li>
        <div>
          <strong>${esc(t("dataPeopleTitle"))}</strong>
          <span>${esc(t("dataOffice", { from, to }))}</span>
          <p class="source-links">${link("https://www.wikidata.org/wiki/Property:P39", "Wikidata P39")}${link("https://es.wikipedia.org/", "Wikipedia")}${link("../data/people.json", t("dataList"), false)}${link("../data/office-corrections.json", t("dataFixes"), false)}</p>
        </div>
      </li>
    </ul>
  `;
}

function rankedShare(key) {
  const ranked = store.leaders.filter((leader) => leader.eligible);
  return {
    have: ranked.filter((leader) => hasValue(leader[key])).length,
    total: ranked.length,
  };
}

function renderMissing() {
  const schools = rankedShare("schools_change");
  const health = rankedShare("health_change");
  const care = rankedShare("care_change");
  const debt = rankedShare("debt_change");
  const real = rankedShare("real_gained");
  const end = store.meta.years[1];
  const blank = health.total - health.have;
  const flagged = store.leaders.find((leader) => leader.health_starts_on_break);
  const spell = flagged.spells.find((item) => item.health_starts_on_break);
  const breakYear = store.meta.health_break_year;
  app.innerHTML = `
    <p class="kicker">${esc(t("missingKicker"))}</p>
    <h1>${esc(t("missingTitle"))}</h1>
    <p class="deck">${esc(t("missingDeck"))}</p>
    <div class="coverage">
      <article class="full">
        <b>${esc(t("shareOf", schools))}</b>
        <p>${esc(t("cardSchools", { from: store.meta.schools_first_year, to: end }))}</p>
      </article>
      <article class="thin">
        <b>${esc(t("shareOf", health))}</b>
        <p>${esc(t("cardHealth", { from: store.meta.health_first_year, to: end }))}</p>
      </article>
      <article class="thin">
        <b>${esc(t("shareOf", care))}</b>
        <p>${esc(t("cardCare", { from: store.meta.care_first_year, to: end }))}</p>
      </article>
    </div>
    <section class="break-story">
      <div class="break-pair">
        <div>
          <span>${esc(t("decLabel", { year: breakYear - 1 }))}</span>
          <b>${number(flagged.health_old_days, 0)}</b>
          <em>${esc(t("daysOld"))}</em>
        </div>
        <div>
          <span>${esc(t("decLabel", { year: breakYear }))}</span>
          <b class="slower">${number(flagged.health_break_open_days, 0)}</b>
          <em>${esc(t("daysNew"))}</em>
        </div>
      </div>
      <p>${esc(t("breakLead", { old: number(flagged.health_old_days, 0), open: number(flagged.health_break_open_days, 0) }))}<a href="${personLink(flagged)}">${esc(flagged.name)}</a>${esc(t("breakTail", { open: number(flagged.health_break_open_days, 0), after: number(spell.health_after, 0) }))}</p>
    </section>
    <h2>${esc(t("asksTitle"))}</h2>
    <ol class="asks">
      ${[1, 2, 3, 4, 5, 6].map((item) => `<li><div><strong>${esc(t(`ask${item}Title`))}</strong><span>${esc(t(`ask${item}Body`, { blank, total: health.total }))}</span></div></li>`).join("")}
    </ol>
    <h2>${esc(t("coverTitle"))}</h2>
    <ul class="compare">
      <li><div><strong>${esc(t("coverSchoolsTitle"))}</strong><span>${esc(t("coverSchools", { from: store.meta.schools_first_year, to: end }))}</span></div><b class="faster">${esc(t("shareOf", schools))}</b></li>
      <li><div><strong>${esc(t("coverHealthTitle"))}</strong><span>${esc(t("coverHealth", { from: store.meta.health_first_year, to: end }))}</span></div><b class="slower">${esc(t("shareOf", health))}</b></li>
      <li><div><strong>${esc(t("coverCareTitle"))}</strong><span>${esc(t("coverCare", { from: store.meta.care_first_year, to: end }))}</span></div><b class="slower">${esc(t("shareOf", care))}</b></li>
      <li><div><strong>${esc(t("coverDebtTitle"))}</strong><span>${esc(t("coverDebt", { from: store.meta.years[0], to: end }))}</span></div><b class="faster">${esc(t("shareOf", debt))}</b></li>
      <li><div><strong>${esc(t("coverRealTitle"))}</strong><span>${esc(t("coverReal", { from: store.meta.years[0], to: end }))}</span></div><b>${esc(t("shareOf", real))}</b></li>
    </ul>
    <p class="note">${esc(t("missingFoot"))}<a href="#/method">${esc(t("missingMethod"))}</a>.</p>
  `;
}

const BUDGET_KEYS = [
  ["health", "commHealth"],
  ["education", "commEducation"],
  ["care", "commCare"],
  ["housing", "commHousing"],
  ["transport", "commTransport"],
  ["interest", "commInterest"],
  ["rest", "commRest"],
];

const SPAIN_TARGET_KEYS = [
  ["justice", "commJustice"],
  ["defence", "commDefence"],
  ["security", "commSecurity"],
  ["foreign", "commForeign"],
  ["employment", "commEmployment"],
  ["unemployment", "commUnemployment"],
  ["benefits", "commBenefits"],
  ["labour", "commLabour"],
  ["social_security", "commSocialSecurity"],
  ["culture", "commCulture"],
  ["agriculture", "commAgriculture"],
  ["farm_works", "commFarmWorks"],
  ["industry", "commIndustry"],
  ["energy", "commEnergy"],
  ["commerce", "commCommerce"],
  ["tourism", "commTourism"],
  ["research", "commResearch"],
  ["economic", "commEconomic"],
  ["leadership", "commLeadership"],
  ["general", "commGeneral"],
  ["statistics", "commStatistics"],
  ["tax", "commTax"],
  ["transfers", "commTransfersAdmin"],
  ["eu_transfers", "commEuBudget"],
  ["communications", "commCommunications"],
  ["community", "commCommunity"],
  ["other_social", "commOtherSocial"],
  ["resilient", "commResilient"],
];

function communityBy(slug) {
  return store.communities.regions.find((region) => region.slug === slug);
}

function lawsFor(slug) {
  return laws.filter((law) => law.region === slug);
}

function kindLabel(kind) {
  if (kind === "decreto-ley") return t("commKindDecree");
  if (kind === "presupuestos") return t("commKindBudget");
  return t("commKindLey");
}

function millions(miles) {
  if (!hasValue(miles)) return "—";
  return `${formatNumber(miles / 1000, 0)} ${t("commMillionUnit")}`;
}

function signedMillions(miles) {
  if (!hasValue(miles)) return "—";
  return `${signed(miles / 1000, 0)} ${t("commMillionUnit")}`;
}

function stockShare(part, total) {
  if (!hasValue(part) || !total) return null;
  return Math.round((part / total) * 1000) / 10;
}

function budgetKeys(budget) {
  const keys = BUDGET_KEYS.filter(([key]) => key !== "rest");
  if (budget.pensions > 0) keys.push(["pensions", "commPensions"]);
  for (const pair of SPAIN_TARGET_KEYS) {
    if (budget[pair[0]] > 0) keys.push(pair);
  }
  if (budget.rest > 0) keys.push(["rest", "commRest"]);
  return keys;
}

const BUDGET_PARTS = {
  general: [
    ["general_territory", "partTerritory"],
    ["general_mutual", "partMutual"],
    ["general_finance", "partFinance"],
    ["general_purchase", "partPurchase"],
    ["general_elections", "partElections"],
    ["general_admin", "partGeneralAdmin"],
    ["general_contingency", "partContingency"],
    ["general_memory", "partMemory"],
    ["staff", "partStaff"],
    ["goods", "partGoods"],
    ["current_transfers", "partCurrentTransfers"],
    ["capital_transfers", "partCapitalTransfers"],
    ["investment", "partInvestment"],
    ["assets", "partAssets"],
    ["contingency", "partFund"],
    ["general_other", "partGeneralOther"],
  ],
  leadership: [
    ["crown", "partCrown"],
    ["parliament", "partParliament"],
    ["constitutional", "partConstitutional"],
    ["audit", "partAudit"],
    ["council", "partCouncil"],
    ["government", "partGovernment"],
    ["leadership_other", "partLeadershipOther"],
  ],
  justice: [
    ["courts", "partCourts"],
    ["judicial_council", "partJudicialCouncil"],
    ["justice_other", "partJusticeOther"],
  ],
  foreign: [
    ["embassies", "partEmbassies"],
    ["cooperation", "partCooperation"],
    ["foreign_other", "partForeignOther"],
  ],
};

function partList(budget, parent) {
  const parts = budget.parts && budget.parts[parent];
  const order = BUDGET_PARTS[parent];
  if (!parts || !order) return "";
  const rows = order.filter(([key]) => parts[key] > 0).map(([key, label]) => {
    const ofGdp = budget.parts_gdp && budget.parts_gdp[parent] && budget.parts_gdp[parent][key];
    const gdpLine = hasValue(ofGdp)
      ? `<small class="of-gdp">${esc(t("commBudgetGdp", { n: number(ofGdp, 2) }))}</small>`
      : "";
    return `<li>
      <span>${esc(t(label))}</span>
      <b>${gdpLine}${number(parts[key], 2)}%</b>
      <i><em style="width:${Math.max(0, parts[key])}%"></em></i>
    </li>`;
  }).join("");
  return rows ? `<ul class="parts">${rows}</ul>` : "";
}

function budgetList(budget) {
  if (!budget) return `<p class="empty">${esc(t("commBudgetMissing"))}</p>`;
  const span = budget.from === budget.to ? `${budget.from}` : `${budget.from}–${budget.to}`;
  const note = budget.complete
    ? ""
    : `<p class="note">${esc(t("commBudgetPartial", { span }))}</p>`;
  const rows = budgetKeys(budget).map(([key, label]) => {
    const ofGdp = budget.of_gdp && budget.of_gdp[key];
    const gdpLine = hasValue(ofGdp)
      ? `<small class="of-gdp">${esc(t("commBudgetGdp", { n: number(ofGdp, 2) }))}</small>`
      : "";
    return `
    <li>
      <span>${esc(t(label))}</span>
      <b>${gdpLine}${number(budget[key])}%</b>
      <i><em style="width:${Math.max(0, budget[key])}%"></em></i>
      ${partList(budget, key)}
    </li>`;
  }).join("");
  const partsNote = budget.parts
    ? `<p class="note">${esc(t(budget.parts.leadership ? "commBudgetPartsSpain" : "commBudgetParts"))}</p>`
    : "";
  return `${note}${partsNote}<ul class="budget${budget.of_gdp ? " budget-gdp" : ""}">${rows}</ul>`;
}

function debtPanel(debt) {
  if (!debt) return `<p class="empty">${esc(t("commNoDebt"))}</p>`;
  const row = (label, part) => {
    const share = stockShare(part, debt.total);
    return `<li>
      <span>${esc(label)}</span>
      <b>${hasValue(share) ? `${number(share)}%` : "—"}</b>
      <i><em style="width:${Math.max(0, share || 0)}%"></em></i>
    </li>`;
  };
  const fund = debt.fund > 0 ? `<p class="note">${esc(t("commFund", { n: millions(debt.fund) }))}</p>` : "";
  return `
    <p class="deck"><strong class="${burden(debt.change)}">${signedMillions(debt.change)}</strong></p>
    <ul class="budget">
      ${row(t("commBonds"), debt.bonds)}
      ${row(t("commLoans"), debt.loans)}
    </ul>
    <p class="note">${esc(t("commBonds"))} ${millions(debt.bonds)}. ${esc(t("commLoans"))} ${millions(debt.loans)}.</p>
    ${fund}`;
}

function volumeChart(region, regionLaws) {
  const points = region.volume;
  const known = points.map((point) => point.level).filter((level) => level !== null);
  if (!known.length) return "";
  const min = Math.min(...known);
  const max = Math.max(...known);
  const pad = Math.max((max - min) * 0.28, 1);
  const low = min - pad;
  const high = max + pad;
  const width = 760;
  const height = 280;
  const left = 46;
  const right = 16;
  const top = 18;
  const bottom = 28;
  const plotW = width - left - right;
  const plotH = height - top - bottom;
  const xOf = (index) => left + (plotW * index) / (points.length - 1);
  const yOf = (value) => top + (plotH * (high - value)) / (high - low);
  const line = points.flatMap((point, index) => (
    point.level === null ? [] : [`${xOf(index).toFixed(1)},${yOf(point.level).toFixed(1)}`]
  ));
  const labels = points.filter((point) => point.year % 5 === 0).map((point) => {
    const index = points.indexOf(point);
    return `<text class="axis" x="${xOf(index).toFixed(1)}" y="${height - 8}" text-anchor="middle">${point.year}</text>`;
  }).join("");
  const spain = yOf(100);
  const base = spain >= top && spain <= top + plotH
    ? `<line class="baseline" x1="${left}" x2="${width - right}" y1="${spain.toFixed(1)}" y2="${spain.toFixed(1)}"/>`
    : "";
  const scale = `<text class="axis" x="4" y="${top + 11}">${max.toFixed(0)}</text><text class="axis" x="4" y="${(top + plotH).toFixed(1)}">${min.toFixed(0)}</text>`;
  const layouts = regionLaws.flatMap((law) => {
    const index = points.findIndex((point) => point.year === law.year);
    const point = points[index];
    if (!point || point.level === null) return [];
    return [{ law, x: (xOf(index) / width) * 100, y: (yOf(point.level) / height) * 100 }];
  });
  const parent = layouts.map((_, index) => index);
  const find = (index) => (parent[index] === index ? index : (parent[index] = find(parent[index])));
  for (let i = 0; i < layouts.length; i += 1) {
    for (let j = i + 1; j < layouts.length; j += 1) {
      if (Math.abs(layouts[i].law.year - layouts[j].law.year) <= 3) parent[find(i)] = find(j);
    }
  }
  const groups = new Map();
  layouts.forEach((item, index) => {
    const key = find(index);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  });
  let maxLane = 0;
  for (const group of groups.values()) {
    const anchor = Math.min(...group.map((item) => item.y));
    group.forEach((item, lane) => {
      item.anchor = anchor;
      item.lane = lane;
      maxLane = Math.max(maxLane, lane);
    });
  }
  const dots = layouts.map(({ law, x, anchor, lane }) => `
    <button type="button" class="law-dot" data-law="${esc(law.id)}" style="left:${x.toFixed(2)}%;top:calc(${anchor.toFixed(2)}% - ${lane * 46}px)" aria-label="${esc(law.title)}"><span></span></button>`).join("");
  const room = maxLane ? maxLane * 46 + 22 : 0;
  return `<div class="chart volume-chart"><div class="plot"><div style="height:${room}px"></div><div class="plot-sheet"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(t(region.reference ? "commChartEu" : "commChart"))}">${base}${scale}<polyline class="series" points="${line.join(" ")}"/>${labels}</svg>${dots}</div></div></div>`;
}

function voteBars(law, side, thin) {
  const rows = law.votes.filter((vote) => vote.side === side);
  if (!rows.length) return `<p class="empty">${esc(t("commVoteNone"))}</p>`;
  const max = Math.max(...law.votes.map((vote) => vote.count), 1);
  return rows.map((vote) => `
    <li class="${thin ? "is-thin" : ""}">
      <span>${esc(vote.group)}</span>
      <i><em style="width:${(100 * vote.count / max).toFixed(1)}%"></em></i>
      <b>${vote.count.toLocaleString(locale())}</b>
    </li>`).join("");
}

function lawPanel(law) {
  if (!law) return `<section class="vote" id="vote" hidden></section>`;
  return `
    <section class="vote is-on" id="vote" data-law="${esc(law.id)}">
      <p class="kicker">${esc(kindLabel(law.kind))} · ${esc(law.voted_on)}</p>
      <h2>${esc(law.title)}</h2>
      <p>${esc(law.sentence)}</p>
      <p class="note">${esc(t("commNote"))}</p>
      <div class="vote-sides">
        <div>
          <h3>${esc(t("commVoteFor"))}</h3>
          <ul class="votes">${voteBars(law, "for", false)}</ul>
        </div>
        <div>
          <h3>${esc(t("commVoteAgainst"))}</h3>
          <ul class="votes against">${voteBars(law, "against", false)}</ul>
        </div>
      </div>
      <h3>${esc(t("commVoteAbstain"))}</h3>
      <ul class="votes abstain">${voteBars(law, "abstain", true)}</ul>
      <p><a href="${esc(law.url)}" target="_blank" rel="noopener">${esc(t("commGazette"))}</a></p>
      <button type="button" class="chip" data-close-law>${esc(t("commClose"))}</button>
    </section>`;
}

function openLaw(id) {
  const law = laws.find((item) => item.id === id);
  const slot = document.querySelector("#vote");
  if (!law || !slot) return;
  slot.outerHTML = lawPanel(law);
  document.querySelectorAll("[data-law]").forEach((node) => {
    node.classList.toggle("is-on", node.dataset.law === id);
  });
  document.querySelector("#vote")?.scrollIntoView({ block: "nearest" });
}

function flowPanel(block, reference) {
  const flow = block.flow;
  if (!flow) return "";
  const span = flow.from === flow.to ? `${flow.from}` : `${flow.from}–${flow.to}`;
  const title = reference ? "commFlowTitleEu" : "commFlowTitle";
  const received = reference ? "commReceivedEu" : "commReceived";
  const returned = reference ? "commReturnedEu" : "commReturned";
  const help = reference ? "commFlowHelpEu" : "commFlowHelp";
  return `
    <h3>${esc(t(title))}</h3>
    <div class="pair">
      <div><span>${esc(t(received))} · ${span}</span><strong>${millions(flow.received)}</strong></div>
      <div><span>${esc(t(returned))} · ${span}</span><strong>${millions(flow.paid)}</strong></div>
      ${reference ? `<div><span>${esc(t("commEuNet"))} · ${span}</span><strong class="${euBalance(flow.net)}">${signedMillions(flow.net)}</strong></div>` : ""}
    </div>
    <p class="note">${esc(t(help))}</p>`;
}

function scaleLine(block, reference) {
  const scale = block.scale;
  if (!scale) return "";
  const bits = [];
  if (hasValue(scale.gdp)) bits.push(t("commScaleLine", { year: scale.year, gdp: millions(scale.gdp) }));
  if (block.debt && hasValue(scale.share)) {
    bits.push(t(reference ? "commScaleDebtSpain" : "commScaleDebt", { debt: millions(block.debt.total), share: `${number(scale.share)}%` }));
  }
  if (hasValue(scale.spent)) bits.push(t(reference ? "commScaleSpentSpain" : "commScaleSpent", { spent: millions(scale.spent) }));
  if (reference && block.state && hasValue(block.state.spent)) bits.push(t("commScaleState", { spent: millions(block.state.spent) }));
  if (hasValue(scale.share_change)) bits.push(t("commBurdenChangeLine", { change: signedPoints(scale.share_change) }));
  if (!bits.length) return "";
  return `<p class="note">${bits.map((bit) => esc(bit)).join(" ")}</p>`;
}

function statePanel(block) {
  const state = block.state;
  if (!state || (!hasValue(state.given) && !hasValue(state.back))) return "";
  const span = state.from && state.to ? (state.from === state.to ? `${state.from}` : `${state.from}–${state.to}`) : "";
  return `
    <h3>${esc(t("commStateTitle"))}</h3>
    <div class="pair">
      <div><span>${esc(t("commStateGiven"))}${span ? ` · ${span}` : ""}</span><strong>${millions(state.given)}</strong></div>
      <div><span>${esc(t("commStateBack"))}${span ? ` · ${span}` : ""}</span><strong>${millions(state.back)}</strong></div>
      <div><span>${esc(t("commStateNet"))}${span ? ` · ${span}` : ""}</span><strong class="${communityBalance(state.net)}">${signedMillions(state.net)}</strong></div>
    </div>
    <p class="note">${esc(t("commStateHelp"))}</p>`;
}

function blockTable(regions, chosen) {
  const reference = regions.some((region) => region.reference);
  const growth = reference ? "commGrowthSpain" : "commGrowth";
  const during = reference ? "commDuringEu" : "commDuring";
  const laterGrowth = reference ? "commLaterGrowthSpain" : "commLaterGrowth";
  const later = reference ? "commLaterEu" : "commLater";
  const received = reference ? "commReceivedEu" : "commReceived";
  const returned = reference ? "commReturnedEu" : "commReturned";
  const spent = reference ? "commSpentAll" : "commSpent";
  const stateCells = (block) => (reference ? `
      <td class="num" data-label="${esc(t("commStateSpent"))}">${millions(block.state && block.state.spent)}</td>
      <td class="num" data-label="${esc(t("commStateGiven"))}">${millions(block.state && block.state.given)}</td>
      <td class="num" data-label="${esc(t("commStateBack"))}">${millions(block.state && block.state.back)}</td>
      <td class="num ${communityBalance(block.state && block.state.net)}" data-label="${esc(t("commStateNet"))}">${signedMillions(block.state && block.state.net)}</td>` : "");
  const rows = regions.map((region) => {
    const block = region.blocks.find((item) => item.id === chosen.id);
    return `<tr>
      <td data-label=""><a href="#/communities/${encodeURIComponent(region.slug)}?window=${encodeURIComponent(chosen.id)}">${esc(region.name)}</a></td>
      <td class="num ${tone(block.growth)}" data-label="${esc(t(growth))}">${signedPercent(block.growth)}</td>
      <td class="num ${tone(block.during)}" data-label="${esc(t(during))}">${signedPercent(block.during)}</td>
      <td class="num" data-label="${esc(t(laterGrowth))}">${block.later_ready ? `<span class="${tone(block.later_growth)}">${signedPercent(block.later_growth)}</span>` : esc(t("commSoon"))}</td>
      <td class="num" data-label="${esc(t(later))}">${block.later_ready ? `<span class="${tone(block.later)}">${signedPercent(block.later)}</span>` : esc(t("commSoon"))}</td>
      <td class="num ${tone(block.balance)}" data-label="${esc(t("commBalance"))}">${signedPercent(block.balance)}</td>
      <td class="num ${tone(block.balance_end)}" data-label="${esc(t("commBalanceEnd"))}">${signedMillions(block.balance_end)}</td>
      <td class="num" data-label="${esc(t(received))}">${block.flow ? millions(block.flow.received) : "—"}</td>
      <td class="num" data-label="${esc(t(returned))}">${block.flow ? millions(block.flow.paid) : "—"}</td>
      ${reference ? `<td class="num ${euBalance(block.flow && block.flow.net)}" data-label="${esc(t("commEuNet"))}">${block.flow ? signedMillions(block.flow.net) : "—"}</td>` : ""}
      ${stateCells(block)}
      <td class="num" data-label="${esc(t("commGdp"))}">${millions(block.scale && block.scale.gdp)}</td>
      <td class="num" data-label="${esc(t(spent))}">${millions(block.scale && block.scale.spent)}</td>
      <td class="num ${burden(block.debt && block.debt.change)}" data-label="${esc(t("commDebt"))}">${block.debt ? signedMillions(block.debt.change) : "—"}</td>
      <td class="num" data-label="${esc(t("commDebtLevel"))}">${block.debt ? millions(block.debt.total) : "—"}</td>
      <td class="num" data-label="${esc(t("commBurden"))}">${hasValue(block.scale && block.scale.share) ? `${number(block.scale.share)}%` : "—"}</td>
      <td class="num ${burden(block.scale && block.scale.share_change)}" data-label="${esc(t("commBurdenChange"))}">${signedPoints(block.scale && block.scale.share_change)}</td>
    </tr>`;
  }).join("");
  return `<div class="table-scroll"><table class="rank blocks"><thead><tr>
      <th></th>
      <th>${esc(t(growth))}</th>
      <th>${esc(t(during))}</th>
      <th>${esc(t(laterGrowth))}</th>
      <th>${esc(t(later))}</th>
      <th>${esc(t("commBalance"))}</th>
      <th>${esc(t("commBalanceEnd"))}</th>
      <th>${esc(t(received))}</th>
      <th>${esc(t(returned))}</th>
      ${reference ? `<th>${esc(t("commEuNet"))}</th>` : ""}
      ${reference ? `<th>${esc(t("commStateSpent"))}</th><th>${esc(t("commStateGiven"))}</th><th>${esc(t("commStateBack"))}</th><th>${esc(t("commStateNet"))}</th>` : ""}
      <th>${esc(t("commGdp"))}</th>
      <th>${esc(t(spent))}</th>
      <th>${esc(t("commDebt"))}</th>
      <th>${esc(t("commDebtLevel"))}</th>
      <th>${esc(t("commBurden"))}</th>
      <th>${esc(t("commBurdenChange"))}</th>
    </tr></thead><tbody>${rows}</tbody></table></div>`;
}

function renderCommunities(params) {
  const pack = store.communities;
  const chosen = pack.windows.find((window) => window.id === params.get("window"))
    || [...pack.windows].reverse().find((window) => window.later_ready);
  const chips = pack.windows.map((window) => `
    <button type="button" class="chip${window.id === chosen.id ? " is-on" : ""}" data-window="${esc(window.id)}">${window.start}–${window.end}${window.open ? ` · ${esc(t("commOpen"))}` : ""}</button>`).join("");
  const spain = pack.regions.filter((region) => region.reference);
  const communities = pack.regions.filter((region) => !region.reference);
  app.innerHTML = `
    <p class="kicker">${esc(t("commKicker"))}</p>
    <h1>${esc(t("commTitle"))}</h1>
    <p class="deck">${esc(t("commDeck"))}</p>
    <p class="note">${esc(t("commNote"))}</p>
    <div class="filters">${chips}</div>
    ${spain.length ? `<h2>${esc(spain[0].name)}</h2>${blockTable(spain, chosen)}` : ""}
    ${blockTable(communities, chosen)}
    <p class="note">${esc(t("commScaleNote"))}</p>
    <p class="note">${esc(t("commFlowNote"))}</p>`;
}

function renderCommunity(slug) {
  const region = communityBy(slug);
  if (!region) {
    app.innerHTML = `<p class="empty">${esc(t("commNoRegion"))}</p>`;
    return;
  }
  const regionLaws = lawsFor(slug).slice().sort((a, b) => a.voted_on.localeCompare(b.voted_on));
  const held = regionLaws.find((law) => law.id === heldLaw) || null;
  const list = regionLaws.length
    ? `<ul class="law-list">${regionLaws.map((law) => `
        <li><button type="button" data-law="${esc(law.id)}"><strong>${esc(law.voted_on.slice(0, 4))}</strong><span>${esc(kindLabel(law.kind))}. ${esc(law.title)}</span></button></li>`).join("")}</ul>`
    : `<p class="empty">${esc(t("commLawsEmpty"))}</p>`;
  const blocks = region.blocks.map((block) => `
    <article class="block" id="block-${esc(block.id)}">
      <h2>${block.start}–${block.end}${block.open ? ` · ${esc(t("commOpen"))}` : ""}</h2>
      ${block.open ? `<p class="note">${esc(t("commBlockOpen"))}</p>` : ""}
      <div class="pair">
        <div><span>${esc(t(region.reference ? "commGrowthSpain" : "commGrowth"))}</span><strong class="${tone(block.growth)}">${signedPercent(block.growth)}</strong></div>
        <div><span>${esc(t(region.reference ? "commDuringEu" : "commDuring"))}</span><strong class="${tone(block.during)}">${signedPercent(block.during)}</strong></div>
        <div><span>${esc(t(region.reference ? "commLaterGrowthSpain" : "commLaterGrowth"))}${block.later_ready ? ` · ${block.later_start}–${block.later_end}` : ""}</span><strong class="${tone(block.later_growth)}">${block.later_ready ? signedPercent(block.later_growth) : esc(t("commSoon"))}</strong></div>
        <div><span>${esc(t(region.reference ? "commLaterEu" : "commLater"))}${block.later_ready ? ` · ${block.later_start}–${block.later_end}` : ""}</span><strong class="${tone(block.later)}">${block.later_ready ? signedPercent(block.later) : esc(t("commSoon"))}</strong></div>
      </div>
      ${!block.open && !block.later_ready ? `<p class="note">${esc(t("commBlockSoon"))}</p>` : ""}
      <h3>${esc(t("commBudget"))}</h3>
      <p class="note">${esc(t(region.reference ? "commBudgetHelpSpain" : "commBudgetHelp"))}</p>
      ${budgetList(block.budget)}
      <h3>${esc(t("commBalanceTitle"))}</h3>
      <div class="pair">
        <div><span>${esc(t("commBalance"))}</span><strong class="${tone(block.balance)}">${signedPercent(block.balance)}</strong></div>
        <div><span>${esc(t("commBalanceEnd"))}${block.scale ? ` · ${block.scale.year}` : ""}</span><strong class="${tone(block.balance_end)}">${signedMillions(block.balance_end)}</strong></div>
      </div>
      <p class="note">${esc(t("commBalanceHelp"))}</p>
      <h3>${esc(t("commDebtTitle"))}</h3>
      <p class="note">${esc(t("commDebtHelp"))}</p>
      ${debtPanel(block.debt)}
      ${flowPanel(block, region.reference)}
      ${region.reference ? statePanel(block) : ""}
      ${scaleLine(block, region.reference)}
    </article>`).join("");
  app.innerHTML = `
    <p class="kicker"><a href="#/communities">${esc(t("commTitle"))}</a></p>
    <h1>${esc(region.name)}</h1>
    ${region.reference ? `<p class="note">${esc(t("commSpain"))}</p>` : region.foral ? `<p class="note">${esc(t("commForal"))}</p>` : ""}
    <p class="note">${esc(t(region.reference ? "commChartEu" : "commChart"))} ${esc(t("commNote"))}</p>
    ${volumeChart(region, regionLaws)}
    ${region.reference ? "" : `${lawPanel(held)}
    <h2>${esc(t("commLaws"))}</h2>
    ${list}`}
    ${blocks}
    ${region.reference ? "" : `<p class="note"><a href="${regionLink(region.slug)}">${esc(t("commPresidents"))}</a></p>`}`;
  if (held) {
    document.querySelectorAll("[data-law]").forEach((node) => {
      node.classList.toggle("is-on", node.dataset.law === held.id);
    });
  }
}

function go(params) {
  const search = new URLSearchParams();
  if (params.verdict && params.verdict !== "all") search.set("verdict", params.verdict);
  if (params.q) search.set("q", params.q);
  const query = search.toString();
  location.hash = query ? `/?${query}` : "/";
}

function applyChrome(page) {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  const switcher = document.querySelector(".lang");
  if (switcher) switcher.setAttribute("aria-label", t("langLabel"));
  document.querySelectorAll("[data-lang]").forEach((button) => {
    const on = button.dataset.lang === lang;
    button.classList.toggle("is-on", on);
    button.setAttribute("aria-pressed", on ? "true" : "false");
  });
  document.querySelectorAll("nav a").forEach((link) => {
    const on = link.dataset.page === page;
    link.classList.toggle("is-on", on);
    if (on) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  const titles = { home: "titleHome", communities: "titleCommunities", method: "titleMethod", data: "titleData", missing: "titleMissing" };
  if (titles[page]) document.title = t(titles[page]);
}

function render() {
  const raw = (location.hash.replace(/^#/, "") || "/");
  const [path, query = ""] = raw.split("?");
  const parts = path.split("/").filter(Boolean);
  const params = new URLSearchParams(query);
  const y = keepScroll ? window.scrollY : 0;
  if (keepScroll) {
    const lab = document.querySelector("#score-lab");
    heldLab = lab ? readLab(lab) : null;
    heldExample = Boolean(document.querySelector(".learn[open]"));
    heldLaw = document.querySelector(".vote.is-on")?.dataset.law || null;
  } else {
    heldLab = null;
    heldExample = false;
    heldLaw = null;
  }
  keepScroll = false;
  let page = "home";
  if (parts[0] === "communities" && parts[1]) {
    page = "communities";
    const slug = decodeURIComponent(parts[1]);
    renderCommunity(slug);
    const community = communityBy(slug);
    if (community) document.title = community.name;
  } else if (parts[0] === "communities") {
    page = "communities";
    renderCommunities(params);
  } else if (parts[0] === "region" && parts[1]) {
    page = "region";
    renderRegion(decodeURIComponent(parts[1]));
    const region = store.regions.find((item) => item.slug === decodeURIComponent(parts[1]));
    if (region) document.title = region.name;
  } else if (parts[0] === "person" && parts[1]) {
    page = "person";
    renderPerson(decodeURIComponent(parts[1]));
    const leader = leaderFor(decodeURIComponent(parts[1]));
    if (leader) document.title = leader.name;
  } else if (parts[0] === "method") {
    page = "method";
    renderMethod();
  } else if (parts[0] === "data") {
    page = "data";
    renderData();
  } else if (parts[0] === "missing") {
    page = "missing";
    renderMissing();
  } else renderHome(params);
  applyChrome(page);
  window.scrollTo(0, y);
  const block = document.getElementById(`block-${params.get("window")}`);
  if (block && !y) block.scrollIntoView();
  if (keepSearchFocus) {
    keepSearchFocus = false;
    const input = document.querySelector("input[name=q]");
    if (input) {
      input.focus();
      const end = input.value.length;
      input.setSelectionRange(end, end);
    }
  }
}

async function start() {
  try {
    const [response, lawsResponse] = await Promise.all([
      fetch("../data/store.json"),
      fetch("../data/laws.json"),
    ]);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    store = await response.json();
    laws = lawsResponse.ok ? await lawsResponse.json() : [];
  } catch (error) {
    app.innerHTML = `<p class="empty">${esc(t("loadError", { error: error.message }))}</p>`;
    return;
  }
  app.addEventListener("click", (event) => {
    const windowButton = event.target.closest("[data-window]");
    if (windowButton) {
      location.hash = `#/communities?window=${encodeURIComponent(windowButton.dataset.window)}`;
      return;
    }
    if (event.target.closest("[data-close-law]")) {
      const slot = document.querySelector("#vote");
      if (slot) slot.outerHTML = lawPanel(null);
      document.querySelectorAll("[data-law].is-on").forEach((node) => node.classList.remove("is-on"));
      return;
    }
    const lawButton = event.target.closest("[data-law]");
    if (lawButton) {
      openLaw(lawButton.dataset.law);
      return;
    }
  });
  document.querySelector(".lang").addEventListener("click", (event) => {
    const button = event.target.closest("[data-lang]");
    if (!button || button.dataset.lang === lang) return;
    lang = button.dataset.lang;
    localStorage.setItem("plan-mery-lang", lang);
    keepScroll = true;
    render();
  });
  window.addEventListener("hashchange", render);
  render();
}

start();
