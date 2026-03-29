def compute_card_classes(cards):
    num_cards = len(cards)
    lg_classes = []
    if num_cards < 3:
        if num_cards == 2:
            lg_classes = ["col-lg-6", "col-lg-6"]
        else:
            lg_classes = ["col-lg-12"]
    elif num_cards % 4 == 0:
        lg_classes = ["col-lg-3"] * num_cards
    elif num_cards % 3 == 0:
        lg_classes = ["col-lg-4"] * num_cards
    elif num_cards % 2 == 0:
        lg_classes = ["col-lg-6"] * num_cards
    else:
        # For complex cases (e.g., 5, 7, 11) – Ensure at least 3 per row
        for i in range(num_cards):
            if num_cards % 4 == 3:
                if i < 3:
                    lg_classes.append("col-lg-4")
                else:
                    lg_classes.append("col-lg-3")
            elif num_cards % 4 == 1:
                if i < 2:
                    lg_classes.append("col-lg-6")
                elif i < 5:
                    lg_classes.append("col-lg-4")
                else:
                    lg_classes.append("col-lg-3")
            elif num_cards % 3 == 2:
                if i < 2:
                    lg_classes.append("col-lg-6")
                else:
                    lg_classes.append("col-lg-4")
    # Use a full-width last card on medium screens only when the total count is odd.
    md_classes = []
    for i in range(num_cards):
        if num_cards % 2 == 0 or i < num_cards - 1:
            md_classes.append("col-md-6")
        else:
            md_classes.append("col-md-12")
    return lg_classes, md_classes
