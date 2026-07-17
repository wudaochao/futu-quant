from futu import KLType, RET_OK, UserSecurityGroupType


WATCHLIST_GROUPS = ("分", "时", "周", "月", "季", "指标")
PERIOD_ORDER = (
    KLType.K_15M,
    KLType.K_60M,
    KLType.K_120M,
    KLType.K_240M,
    KLType.K_WEEK,
    KLType.K_MON,
    KLType.K_QUARTER,
)
PERIOD_LABELS = {
    KLType.K_15M: "15分钟",
    KLType.K_60M: "1小时",
    KLType.K_120M: "2小时",
    KLType.K_240M: "4小时",
    KLType.K_WEEK: "周线",
    KLType.K_MON: "月线",
    KLType.K_QUARTER: "季线",
}


def is_a_share(code):
    return code.startswith(("SH.", "SZ."))


def is_hk_or_us(code):
    return code.startswith(("HK.", "US."))


def all_bbi_boll_tasks(periods):
    return {
        (period, indicator_name)
        for period in periods
        for indicator_name in ("BBI", "BOLL")
    }


def indicator_group_tasks_for(code):
    if is_a_share(code):
        periods = (
            KLType.K_15M,
            KLType.K_60M,
            KLType.K_120M,
            KLType.K_WEEK,
            KLType.K_MON,
            KLType.K_QUARTER,
        )
    else:
        periods = (
            KLType.K_60M,
            KLType.K_240M,
            KLType.K_WEEK,
            KLType.K_MON,
            KLType.K_QUARTER,
        )
    return all_bbi_boll_tasks(periods)


def tasks_for(group_name, code):
    intraday_long = KLType.K_120M if is_a_share(code) else KLType.K_240M
    rules = {
        "分": {
            (KLType.K_15M, "BBI"),
            (KLType.K_15M, "BOLL"),
            (intraday_long, "BBI"),
        },
        "时": {
            (KLType.K_60M, "BBI"),
            (KLType.K_60M, "BOLL"),
            (intraday_long, "BBI"),
            (intraday_long, "BOLL"),
            (KLType.K_WEEK, "BBI"),
        },
        "周": {
            (KLType.K_WEEK, "BBI"),
            (KLType.K_WEEK, "BOLL"),
            (KLType.K_MON, "BBI"),
        },
        "月": {
            (KLType.K_MON, "BBI"),
            (KLType.K_MON, "BOLL"),
            (KLType.K_QUARTER, "BBI"),
        },
        "季": {
            (KLType.K_QUARTER, "BBI"),
            (KLType.K_QUARTER, "BOLL"),
        },
        "指标": indicator_group_tasks_for(code),
    }
    return rules[group_name]


def period_label(period):
    return PERIOD_LABELS.get(period, str(period))


def describe_indicator_tasks(code, tasks):
    grouped = {}
    for period, indicator_name in tasks:
        grouped.setdefault(period, set()).add(indicator_name)

    parts = []
    for period in PERIOD_ORDER:
        indicators = grouped.get(period)
        if not indicators:
            continue
        parts.append(
            "%s %s" % (period_label(period), "/".join(sorted(indicators)))
        )
    return "%s -> %s" % (code, ", ".join(parts))


def load_indicator_tasks(quote_ctx, code_filter=lambda code: True):
    """Load the custom groups and merge tasks for duplicate stocks."""
    ret, groups = quote_ctx.get_user_security_group(
        group_type=UserSecurityGroupType.CUSTOM
    )
    if ret != RET_OK:
        raise RuntimeError("get_user_security_group failed: %s" % groups)

    print(groups)
    available = set(groups["group_name"].tolist())
    tasks = {}
    for group_name in WATCHLIST_GROUPS:
        if group_name not in available:
            continue
        ret, securities = quote_ctx.get_user_security(group_name)
        if ret != RET_OK:
            print("get_user_security error: group=%s, msg=%s" % (group_name, securities))
            continue
        for code in securities["code"].dropna().unique().tolist():
            print(code)
            if code_filter(code):
                tasks.setdefault(code, set()).update(tasks_for(group_name, code))
    return tasks
