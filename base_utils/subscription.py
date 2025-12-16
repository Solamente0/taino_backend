from django.contrib.auth import get_user_model

User = get_user_model()


def check_bypass_user_payment(user: User, bypass_rules: list[str], valid_static_name: str) -> bool:
    print(f"{bypass_rules=}", flush=True)
    print(f"{type(bypass_rules)=}", flush=True)
    print(f"{valid_static_name=}", flush=True)
    if not type(bypass_rules) == list:
        bypass_rules = bypass_rules.split(",")
    if not user or not bypass_rules:
        return False
    # bypass_rules example: [lawyer-v_x-free,client-v_plus_pro-premium]
    for rule in bypass_rules:
        print(f"{rule=}", flush=True)
        rule = rule.strip()  # Remove any whitespace
        if not rule:
            continue

        # Split each rule into its components
        try:
            parts = rule.split("-")
            if len(parts) < 3:
                continue  # Skip malformed rules
            print(f"{parts=}", flush=True)

            role = parts[0]
            service_static_name = parts[1]
            need_subscription = parts[2]

            print(f"{role=}", flush=True)
            print(f"{service_static_name=}", flush=True)
            print(f"{need_subscription=}", flush=True)
            if not (service_static_name == valid_static_name):
                continue
            # Check if user has the required role
            if not (user.role and user.role.static_name == role):
                continue  # User doesn't have this role, check next rule

            print(f"{user.role.static_name=}", flush=True)
            print(f"{role=}", flush=True)

            # Check subscription requirement
            if need_subscription == "free":
                # Free access - any user with the role can access
                print(f"free access !!!!!", flush=True)
                return True
            elif need_subscription == "premium":
                # Premium required - only premium users with the role can access
                print(f"does premium access ?????", flush=True)
                if user.has_premium_account:
                    print(f"has premium access !!!!!", flush=True)
                    return True

        except (IndexError, AttributeError) as e:
            print(f"malformed rulesssss!!!! {e=}", flush=True)
            # Skip malformed rules
            continue

    return False
