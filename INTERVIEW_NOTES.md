# Interview notes: Mumbai Property Price Lab

Live app: https://eshan-property-price.streamlit.app/

## The 2-minute story

> "I wanted a project close to what a developer like L&T Realty does every day: pricing flats and new launches in
> Mumbai.
>
> I started with the popular six-city housing dataset on Kaggle, and the first thing I did was check it. In 70% of the
> rows price had almost no relationship with area (correlation 0.2 against 0.85 in the rest), while area and bedrooms
> still matched. The price column was misaligned. So I rejected it and used a cleaner one: 76,000 Mumbai listings from
> Makaan.com.
>
> 27% of those rows were duplicates. I removed them, because otherwise the same flat ends up in training and test and
> the model looks better than it is. I grouped 175 localities into 7 zones and built location features that borrow
> strength: a project with one listing leans on its locality's price; one with 100 listings speaks for itself.
>
> Then I tested four models three ways. A random split gave ±9% error, but that flatters the model, because flats from
> the same project sit on both sides. When I held out whole projects, the developer's real case of pricing a new
> launch, the error was ±13%. Every price comes with an 80% range, and I checked that it really holds 80% in every
> zone.
>
> I also found what drives prices with a fixed-effects regression, and used K-Means to split the market into five
> buyer segments. The key insight: ₹1 crore buys either 550 sq ft in the suburbs or 1,090 sq ft further out. Buyers
> choose location or space, and a developer chooses which of them to build for."

**Why this project:** the L&T Realty role asks for regression, classification and clustering on real-estate data. This
covers regression (price), clustering (segments) and the business questions behind them: launch pricing, price
drivers and who the buyer is.

---

## Data and cleaning

**Where's the data from?** "Mumbai House Prices" on Kaggle (Dravid Vaishnav), 76,038 listings scraped from Makaan.com:
BHK, type, project, area, price, locality, under construction or ready, new or resale.

**What are its limits?** Asking prices, not registered sale prices. One snapshot, no dates, so no trends. No floor,
view, amenities or builder. Area mixes carpet and built-up.

**Why remove duplicates?** 20,312 rows (27%) were the same flat posted again. If the same flat is in training and test,
the model is graded on flats it has already seen. It's a leak.

**How did you handle outliers?** Price per sq ft in the extreme 0.5% at either end, and anything 3x above or below its
locality's typical value (likely typos: wrong unit, missing zero). Every rule is counted; nothing is dropped silently.

**Tell me about the dataset you rejected.** Each city's file was two batches. Where all amenities were coded 9 ("not
mentioned"), area and bedrooms still agreed (correlation ~0.8) but price barely related to either (~0.2). In real
housing data price always rises with size. So the price column was misaligned with the row: a scraping error. Most
people train on it anyway; I checked first.

---

## Features (likely questions)

**How do you encode 175 localities and 9,500 projects?** Target encoding with shrinkage. For each project, the average
log price per sq ft, pulled towards its locality's average when it has few listings:
`(sum of its listings + 5 × locality value) / (its listings + 5)`. Same for locality → zone and zone → Mumbai.

**Isn't target encoding leaky?** It is if a row sees its own price. So training rows get their encoding *out of fold*:
computed from the other 4 folds only. And for the "new project" model the inner folds hold out whole projects too, so
it's trained exactly the way it's used.

**Why log price?** Prices are skewed (₹20 lakh to ₹20 crore) and errors are multiplicative: being ₹10 lakh off on a
₹50 lakh flat is much worse than on a ₹5 crore flat. In logs, errors become percentages.

**What's the monotonic constraint?** Gradient boosting is told price can only go up with area. Without it, a 1,000 sq ft
flat was sometimes priced below a 975 sq ft one in the same place. It cost 0.2 points of accuracy; a client would lose
trust in a tool that does that.

---

## Models and testing

| | Known project | New project | New locality |
|---|---|---|---|
| Baseline: locality ₹/sq ft × area | ±15.8% | ±16.2% | ±27.9% |
| Linear regression | ±13.6% | ±13.9% | ±25.8% |
| Random forest | ±8.4% | ±12.5% | ±27.2% |
| Gradient boosting (deployed) | ±9.2% | ±12.7% | ±25.1% |

Median absolute % error, 5-fold cross-validation.

**Why three tests?** A random split puts flats from the same project in training and test. That's realistic for a new
listing in an existing project, but not for a new launch. Holding out whole projects (grouped K-fold) is the developer's
case. Holding out whole localities shows how far the model can travel.

**Why always compare to a baseline?** "Locality price per sq ft × area" is what a broker does in their head. A model
only earns its place if it beats that: 15.8% → 9.2% for known projects, 16.2% → 12.7% for new ones.

**Linear regression vs random forest, what's the difference?** Linear regression fits one straight-line effect per
feature: easy to explain, can extrapolate. A random forest averages many decision trees on random samples: captures
interactions (a 3 BHK premium that differs by zone) but can't predict beyond what it has seen. Gradient boosting builds
trees one after another, each fixing the previous one's errors.

**Why deploy gradient boosting if the forest is slightly better?** The forest was 0.8 points better on known projects
but its file was 98 MB against under 2 MB: too big for a free web app and slow to load. A small accuracy loss for a
product that actually works.

**What metrics and why?** Median absolute % error (what a person understands: "typically within ±13%"), share within
±10% and ±20%, and R² on log price. Median, not mean, because a few luxury flats would dominate a mean.

**How do you know the price range is honest?** The range is the middle 80% of the model's own cross-validated errors.
I set the limits on 4 folds and checked coverage on the 5th (cross-conformal). One width for all of Mumbai held 80%
overall but only 66% in South Mumbai and 91% in Mira Road, so each zone gets its own width; now every zone is at 80%.

**Where is the model weakest?** South Mumbai and Thane: a sea view or a lake-facing tower changes the price and the
data can't see it. With floor, view and amenities I'd expect a big improvement.

---

## Price drivers

From OLS on log price with a fixed effect for each locality (R² 0.92), so every effect compares flats in the same
locality. Standard errors clustered by project, because flats in one project aren't independent.

| | Effect |
|---|---|
| 10% more area (same BHK) | +5.1% |
| 3 BHK vs 2 BHK, same stated area | +33% |
| Under construction vs ready | +1.8% (95%: +0.6 to +3.1) |
| Resale vs new | −3.9% |
| Studio vs 1 BHK | −28% |

**Why does a bedroom matter more than area?** Listings mix carpet area (what you walk on, required for new projects
under RERA) and built-up / super built-up (often 20-40% bigger). The bedroom count isn't affected by that, so it
carries real size information. A data-quality finding, not a market one.

**No discount for under-construction?** On average, under-construction flats list at the same price per sq ft as
ready ones. New projects come with newer buildings and amenities, which offsets the wait. Only Kalyan-Dombivli shows a
clear premium (+5.7%), where new townships compete with older buildings.

**Is that causal?** No. These are associations in asking prices. Anything the data doesn't record (floor, builder) can
move with them.

**Permutation importance?** Shuffle a group of features and see how much worse the model gets. For a new project:
location +34 points, size +29, status and new/resale under 1. I shuffled groups together because correlated features
(area and BHK) would otherwise share and hide their importance.

---

## Segments (K-Means)

**Which features and why?** Log area (how big) and log price per sq ft (how premium the location), standardised. Those
are the two things every buyer trades off; price is just their product.

**How did you choose k = 5?** The silhouette score is flat from 3 to 7 (0.35-0.38): the market is a smooth spread, not
separate islands, so no k is "correct". I chose 5 because each segment is a buyer you can name and market to. I checked
stability: five other random starts give the same segments (adjusted Rand index 0.99).

**What does K-Means do?** Picks k centres, assigns each point to the nearest centre, moves each centre to the middle of
its points, and repeats until nothing changes. It needs scaled features, otherwise the one with bigger numbers
dominates.

| Segment | Buyer | Budget (middle half) | Typical |
|---|---|---|---|
| Budget starter homes | First-time buyers | ₹33-58 L | 672 sq ft 1 BHK, far suburbs |
| Spacious value homes | Growing families | ₹84 L-1.3 Cr | 1,090 sq ft 2 BHK, Navi Mumbai |
| Compact city homes | Young professionals | ₹71 L-1.14 Cr | 550 sq ft 1 BHK, central suburbs |
| Premium family homes | Established professionals | ₹1.65-2.55 Cr | 970 sq ft 2 BHK, western suburbs |
| Large luxury homes | Senior executives, business owners | ₹2.85-5.75 Cr | 1,800 sq ft 3 BHK, Worli |

**Honest limit:** the data has homes, not buyers. The buyer labels are my interpretation. With CRM data (enquiries,
bookings) I'd cluster the buyers themselves.

---

## Business use (L&T Realty angle)

**How would a developer use this?** The Launch planner: pick a locality and a unit mix (60 1 BHKs, 100 2 BHKs, 40 3 BHKs),
get a price per unit with a range, the total sales value, and where the project's price per sq ft sits against the
projects already selling there. Then decide: price at the market, or justify a premium with amenities and brand.

**What would you add with company data?** Actual sale prices and dates (trends, absorption), floor and view, amenities,
builder brand, and enquiry data, so the segments become real buyer segments and a classification model can predict which
leads will book.

**Why a sign-in page?** Property sites capture leads before showing prices, so I built the same flow: name
plus mobile or email, checked (a 10-digit Indian mobile starting 6-9, or a valid email), with *Skip for now* so
nobody is forced. Sign-ins go to a private Google Sheet through a secret web-hook URL kept in Streamlit's
Secrets, never in the code. If saving fails, the visitor still gets in.

**Why line drawings, not photos?** Everything is drawn in code, so there's nothing to license, and the drawings
carry data: each locality's skyline is taller where prices are higher, and the floor plan redraws with the flat
type. The bars under the price are the model's real past errors in that zone, not decoration.

## Numbers to remember

| | |
|---|---|
| Data | 76,038 listings → 54,598 after cleaning (20,312 duplicates); 175 localities, 9,477 projects, 7 zones |
| Error | ±9% known project, ±13% new project (baseline 16%); 82% / 69% within ±20% |
| Ranges | 80% range holds 80% in every zone (one width: 66% in South Mumbai) |
| Location | South Mumbai ₹31,200/sq ft vs Kalyan-Dombivli ₹5,900 (5.3x) |
| Drivers | 3 BHK +33% vs 2 BHK at the same area; resale −3.9%; under construction +1.8% |
| Segments | 5 segments; silhouette 0.36; stable across seeds (ARI 0.99) |
| Rejected data | price vs area correlation 0.2 vs 0.85: price column misaligned in 70% of rows |
