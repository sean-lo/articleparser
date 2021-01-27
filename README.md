# articleparser
Extracts structured data from web documents.

If you've ever needed to automatically extract the content of web articles, you know how non-straightforward it can get. This project extracts the article text, authors, title, and more - with one command.

## Installation
Install with `pip install articleparser`.
Requires Python 3.8+, and the following dependencies:

```
beautifulsoup4>=4.8
django>=3.0
html5lib>=1.1
language-tags>=1.0.0
lxml>=4.5.0
python-dateutil>=2.8.0
```

## Usage
Example usage:

```
from articleparser.article import Article

# this is a filepath to a HTML document.
filepath = "/path/to/html/document.html"

a = Article(filepath)
a.parse()
```

The parsed content will then be stored in `a.content`. The following is an example from [the Guardian](https://www.theguardian.com/world/2020/sep/05/america-covid-autumn-winter-coronavirus):

```
{
    "record_categories_list": [
        "World news"
    ],
    "author_list": [
        {
            "name": "Dominic Rushe",
            "url": "https://www.theguardian.com/profile/dominic-rushe",
            "image_url": null
        },
        {
            "name": "Amanda Holpuch",
            "url": "https://www.theguardian.com/profile/amanda-holpuch",
            "image_url": null
        }
    ],
    "record_title": "The bleak Covid winter? America still not on course to beat back the virus",
    "record_url": "https://www.theguardian.com/world/2020/sep/05/america-covid-autumn-winter-coronavirus",
    "record_published_isotimestamp": "2020-09-05T09:00:03+00:00",
    "record_modified_isotimestamp": "2020-09-05T09:02:14+00:00",
    "site": [
        {
            "name": "the Guardian",
            "url": null
        }
    ],
    "record_language": "en",
    "record_content": [
        "Even with three decades of experience in the travel industry, Jorge Pesquera has never seen a downturn in business like this one.",
        "Summer officially ends on Monday in the US, and now is the time when many people in colder climes in North America and across the world start dreaming about a winter break on Florida\u2019s golden shores.",
        "Not this year.",
        "The US is closed for many outside its borders, and many within are too scared to fly as Covid continues its deadly sweep across the country. The rate of infection has eased in Florida and elsewhere and Pesquera, president of the marketing group Discover the Palm Beaches, is hopeful business is improving. But it comes in a year of catastrophic collapse for Florida\u2019s tourism.",
        "\u201cNobody has seen anything like this in a couple of generations,\u201d said Pesquera.",
        "As the US enters its first coronavirus winter, economists and epidemiologists see a pivotal moment \u2013 a hinge whose swing will determine the direction of the economy and the course of the disease into 2021 and for years \u2013 potentially generations \u2013 to come.",
        "The US announced its first death from the coronavirus in February. Donald Trump predicted it would be over by Easter \u2013 that hope was pushed back to summer as deaths and infections soared. Seven months on, the US is still not on course to control the pandemic.",
        "Soon Covid-19 will have accounted for 200,000 deaths, and reported cases have already reached 6m. By 1 January, the US coronavirus death toll could reach over 410,000 according to a forecast by researchers at the University of Washington\u2019s Institute for Health Metrics and Evaluation (IHME). Researchers said the projection is based on the \u201crollercoaster\u201d of cases in the US, where governments and individuals take up protective measures when things get bad, then let them slide when the local situation improves, potentially restarting the cycle all over again.",
        "The virus has hit Florida particularly hard. At least 630,000 people have been infected and more than 11,000 have died. Tourism has plummeted. In the second quarter \u2013 April, May and June \u2013 60% fewer people traveled to Florida compared with the same period in 2019 \u2013 a decline of almost 20 million visitors.",
        "Pesquera is confident Florida will bounce back, and hotel occupancies have been climbing as locals and tourists from neighboring states get in their cars and head for a beach break. While he is hopeful that the worst is over, Pesquera said it will be a hard winter and beyond for many in the industry.",
        "But there are now worrying signs that the Covid-19 recession is reaching beyond the travel, leisure and hospitality industries that were hit so hard in the early months of the pandemic. Some of the changes will be long-lasting and some may well be permanent.",
        "Already the pandemic has widened income inequality in the US. Economists including Peter Atwater, a lecturer in the economics department at William & Mary, have begun talking of a \u201cK-shaped\u201d recovery \u2013 where the well-off thrive on the uptick of the K as stock markets and house prices rise, while the working poor fall further behind on the downtick.",
        "The divide has once again highlighted the racial and gender wealth divide in the US. Women, Black and Latinx Americans are losing more jobs than their male, white peers and as the US goes into winter, there are signs that more of that is to come.",
        "Retail, too, was crushed by quarantine measures. With 14.7m jobs, retail is the largest private employer in the country. Employment has declined sharply as online sales have picked up. The industry is dominated by women and people of color. Dozens of retailers have filed for bankruptcy since the pandemic struck, and others are hanging by a thread. The sector has regained some ground in recent months but is still down a million jobs from last year. More may soon be lost, said Jason Reed, assistant chair of finance at the University of Notre Dame.",
        "With summer gone, the shopping season is approaching. This year Walmart will be closed on Thanksgiving for the first time in 30 years and so will Target, Best Buy and Kohl\u2019s. The closures are around safety issues \u2013 the chance of spreading the disease at a door-crushing super-sale is just too high \u2013 but for Reed the closures are a sign of things to come.",
        "\u201cE-commerce has exploded [since the pandemic began],\u201d said Reed. \u201cIt\u2019s like we have done 10 years of growth in a few months. Consumers are getting used to shopping online. I just don\u2019t see jobs coming back in that sector, and that is a huge number of people.\u201d",
        "Other changes, like the collapse of travel, may be temporary, but they will contribute to a dark winter for many. Reed points to the fact that many offices across the US are still closed, a situation that is already shuttering businesses reliant on office workers in city centers. \u201cSo many of these businesses are going to go under, if they haven\u2019t already,\u201d he said.",
        "And these closures are feeding into the wider economy, eroding the tax base of cities and states and threatening swingeing job cuts. Employment in the sector is at levels unseen since 2001. New York alone is considering 22,000 jobs cuts, and Florida has a $1.9bn shortfall in its budget. The Economic Policy Institute has warned that without more federal aid, currently deadlocked in Congress, 5.3m local government jobs could go by the end of 2021. Again, women and people of color will be overrepresented in those jobs losses.",
        "Unemployment has dipped back down over the last few months, reaching 8.4% in August. But the rate is still as high as the peak in the last recession and weekly claims for unemployment insurance have remained historically high at close to 1m a week.",
        "\u201cThe sense that this situation is short-lived and temporary is over,\u201d said Atwater. \u201cFurloughs are becoming permanent layoffs ,and the psychological damage that will do to consumer confidence is going to be a problem.\u201d",
        "Even companies that are doing well are not immune to this pivot, said Atwater. Companies \u2013 particularly in the tech sector \u2013 that have seen their share prices soar to sky-high valuations are now looking for ways to keep those share prices high. Atwater pointed to the recent announcement from Salesforce that it was shedding 1,000 jobs, even as the software company announced bumper sales.",
        "For many of these companies their share prices are now \u201cso high that they are scared to disappoint investors, and they are looking at cost-cutting to keep those share prices levitated,\u201d he said.",
        "Only a fundamental breakthrough in treating Covid-19 is likely to stop winter\u2019s woes. And as the temperature drops and the leaves turn, there is little sign that one is coming soon.",
        "Public health experts say the steps for reining in this pandemic are well established, and it is possible to control the spread of coronavirus in the US within months. To do so, the US would need to be in a position where it could depend on the public health interventions of rapid testing, contact tracing, isolation and quarantine to manage coronavirus cases, instead of depending on drastic measures such as having people work from home and keep their children out of school.",
        "But without the government taking such steps, and maintaining them, the US could again soon be in the position it was in in June and July, when cases surged around the country, warned Caitlin Rivers, an epidemiologist at the Johns Hopkins Center for Health Security.",
        "\u201cWhat I fear is we will just see continuous hotspots coming and going around the country until we get a vaccine,\u201d Rivers said. \u201cThat\u2019s what we don\u2019t want.\u201d",
        "With her colleagues at Johns Hopkins, Rivers identified 10 recommendations for the US to reset its approach to coronavirus in a late July report. The recommendations include to scale up contact tracing, bolster personal protective equipment supplies and test supply chains and close higher-risk activities in places where the epidemic is worsening.",
        "The number of cases recorded each day has drifted down from the peak, and testing is happening more frequently than in the spring, but coronavirus is still spreading an \u201cenormous\u201d amount in communities, Rivers said.",
        "\u201cIt is very widespread around the country,\u201d Rivers said. \u201cAnd we still don\u2019t have as much diagnostic testing as we would like in order to be confident we are catching those cases. I think we still do have a long ways to go before we can feel like we are on track to be in a better place.\u201d",
        "Looking ahead, Rivers said two social factors were bringing \u201cnew urgency\u201d to stop the spread: school closures and people\u2019s hopes to see family during the winter holidays.",
        "\u201cIt\u2019s been five or six [months], and it just seems like we are not heading anywhere purposefully,\u201d Rivers said. \u201cWe are rather drifting along. So if we want to get to a better place, we have to set out the course for that. In some ways, the critical moment now is that if we want to be in a better spot we need to orient ourselves to that goal.\u201d",
        "Saskia Popescu, an infectious disease epidemiologist and infection preventionist, said the US has been consistently struggling to respond to coronavirus since it emerged.",
        "\u201cWe really haven\u2019t seen a time where we\u2019ve been able to wrap our arms around this,\u201d Popescu said. \u201cI think that the continued messaging from the White House down to the local state governors \u2013 that this is not that bad, or [that] we have it under control when we really don\u2019t \u2013 has been really dangerous and misleading.\u201d",
        "In addition to improved rapid testing and contact tracing, Popescu said she wanted to see better leadership from federal and state officials.",
        "Scientists have a much better understanding of how coronavirus is transmitted now, compared with when it first emerged. But they are fighting a tidal wave of mistrust from people who think shifts in messaging are something to be skeptical of, instead of a sign of evolving knowledge, and others who are pushing misinformation.",
        "\u201cWe need leadership across the country to be on the same page, to be supporting and promoting science and ultimately working to reduce transmission consistently, through masking, through ensuring adequate testing, all of those things,\u201d Popescu said.",
        "The slightly more positive figures reported in August put the country in a better position to control the virus compared with when cases were surging around the country, but improvements come with their own challenges. \u201cI do think it is really hard when cases start to decrease to maintain people\u2019s attention and vigilance on it,\u201d Popescu said.",
        "Complacency will only lengthen the pain \u2013 economic and otherwise \u2013 of a pandemic that is already fundamentally reshaping the US for years to come and a virus that doesn\u2019t care what we think about the latest research on masks or social distancing. \u201cWe just don\u2019t know how long this is going to last,\u201d said Reed.",
        "\u2026 joining us from Singapore, we have a small favour to ask. Millions are flocking to the Guardian for open, independent, quality news every day, and readers in 180 countries around the world now support us financially.",
        "We believe everyone deserves access to information that\u2019s grounded in science and truth, and analysis rooted in authority and integrity. That\u2019s why we made a different choice: to keep our reporting open for all readers, regardless of where they live or what they can afford to pay.",
        "The Guardian has no shareholders or billionaire owner, meaning our journalism is free from bias and vested interests \u2013 this makes us different. Our editorial independence and autonomy allows us to provide fearless investigations and analysis of those with political and commercial power. We can give a voice to the oppressed and neglected, and help bring about a brighter, fairer future. Your support protects this.",
        "Supporting us means investing in Guardian journalism for tomorrow and the years ahead. The more readers funding our work, the more questions we can ask, the deeper we can dig, and the greater the impact we can have. We\u2019re determined to provide reporting that helps each of us better understand the world, and take actions that challenge, unite, and inspire change.",
        "Your support means we can keep our journalism open, so millions more have free access to the high-quality, trustworthy news they deserve. So we seek your support not simply to survive, but to grow our journalistic ambitions and sustain our model for open, independent reporting.",
        "If there were ever a time to join us, and help accelerate our growth, it is now. You have the power to support us through these challenging economic times and enable real-world impact.",
        "Every contribution, however big or small, makes a difference. Support us today from as little as $1 \u2013 it only takes a minute. Thank you."
    ],
    "record_description": "As summer ends, and as deaths near 200,000 amid severe economic damage, experts say the next few months are vital",
    "record_images_list": [
        {
            "url": "https://i.guim.co.uk/img/media/f2bbbcd7f97d258a8e3a34aeb7f7fca2d3454c5a/0_0_4000_2667/master/4000.jpg?width=1300&quality=45&auto=format&fit=max&dpr=2&s=64bc860a5fc06ab269832f55aebfe4b3",
            "alt_text": "A rainy Miami Beach. The virus had hit Florida particularly hard, and its tourism industry had been ravaged. Photograph: Crist\u00f3bal Herrera/EPA"
        },
        {
            "url": "https://i.guim.co.uk/img/media/210dbb9016a07b7550cae15fb7767542c5b91568/0_0_3000_2000/master/3000.jpg?width=860&quality=45&auto=format&fit=max&dpr=2&s=dcfe20244e7b809401fa3e5a39a94616",
            "alt_text": "An ice-cream store in Key West in March. Photograph: Joe Raedle/Getty Images"
        },
        {
            "url": "https://i.guim.co.uk/img/media/f51551f5335e9499c51c2b41dc8d8a20b026f6c9/0_0_6240_4160/master/6240.jpg?width=860&quality=45&auto=format&fit=max&dpr=2&s=c3638021539efe1ad2487d58300519cb",
            "alt_text": "A woman walks by a closed business in Brooklyn in July. Photograph: Spencer Platt/Getty Images"
        },
        {
            "url": "https://i.guim.co.uk/img/media/37079f8b236119fef568d05dcce745c7d3170ab1/0_0_3000_2000/master/3000.jpg?width=860&quality=45&auto=format&fit=max&dpr=2&s=b7a94840b1cc967342fedf1a305ccbd1",
            "alt_text": "Nurses protest against the lack of PPE in St Petersburg, Florida. Photograph: Octavio Jones/Reuters"
        },
        {
            "url": "https://i.guim.co.uk/img/media/c88b9398ca57aa1814aa95fe9314e886204fccb2/0_0_5040_3360/master/5040.jpg?width=860&quality=45&auto=format&fit=max&dpr=2&s=9872f2abf4de4f987523eb0ef533498d",
            "alt_text": "Friends and family mourn the death of Conrad Coleman, who died of Covid in New Rochelle, New York, two months after his father died. Photograph: John Moore/Getty Images"
        },
        {
            "url": "https://assets.guim.co.uk/images/acquisitions/2db3a266287f452355b68d4240df8087/payment-methods.png",
            "alt_text": "Accepted payment methods: Visa, Mastercard, American Express  and Paypal"
        }
    ],
    "record_links_list": [
        {
            "url": "https://www.thepalmbeaches.com/",
            "text": "Discover the Palm Beaches"
        },
        {
            "url": "https://www.theguardian.com/us-news/donaldtrump",
            "text": "Donald Trump"
        },
        {
            "url": "https://covid19.healthdata.org/united-states-of-america?view=total-deaths&tab=trend",
            "text": "forecast by researchers"
        },
        {
            "url": "https://www.theguardian.com/us-news/2020/aug/16/us-inequality-coronavirus-pandemic-unemployment",
            "text": "widened income inequality"
        },
        {
            "url": "https://www.theguardian.com/business/2020/aug/04/shecession-coronavirus-pandemic-economic-fallout-women",
            "text": "Women"
        },
        {
            "url": "https://www.theguardian.com/us-news/2020/apr/28/african-americans-unemployment-covid-19-economic-impact",
            "text": "Black"
        },
        {
            "url": "https://www.theguardian.com/business/2020/may/29/us-coronavirus-layoffs-hispanic-americans-hit-hardest",
            "text": "Latinx"
        },
        {
            "url": "https://cepr.net/wp-content/uploads/2020/04/2020-04-Frontline-Workers.pdf",
            "text": "dominated by women and people of color"
        },
        {
            "url": "https://www.pewtrusts.org/en/research-and-analysis/articles/2020/06/16/how-covid-19-is-driving-big-job-losses-in-state-and-local-government",
            "text": "levels unseen since 2001"
        },
        {
            "url": "https://www.epi.org/blog/without-federal-aid-to-state-and-local-governments-5-3-million-workers-will-likely-lose-their-jobs-by-the-end-of-2021-see-estimated-job-losses-by-state/#:~:text=and%20David%20Cooper-,Without%20federal%20aid%20to%20state%20and%20local%20governments%2C%205.3%20million,local%20governments%20in%20coming%20months.",
            "text": "5.3m local government jobs"
        },
        {
            "url": "https://www.epi.org/blog/cuts-to-the-state-and-local-public-sector-will-disproportionately-harm-women-and-black-workers/",
            "text": "women and people of color"
        },
        {
            "url": "https://www.usatoday.com/story/money/2020/08/26/salesforce-job-cuts-stock-employees/5634780002/",
            "text": "shedding 1,000"
        },
        {
            "url": "https://www.centerforhealthsecurity.org/our-work/publications/resetting-our-response-changes-needed-in-the-us-approach-to-covid-19",
            "text": "in a late July report"
        }
    ],
    "record_videos_list": [],
    "record_documents_list": [
        {
            "url": "https://cepr.net/wp-content/uploads/2020/04/2020-04-Frontline-Workers.pdf",
            "alt_text": "dominated by women and people of color"
        }
    ],
    "record_keywords_list": [
        "US news",
        "World news",
        "US politics",
        "Donald Trump",
        "Coronavirus outbreak",
        "US economy",
        "Business"
    ],
    "record_comment_areas_list": []
}
```

## Versioning
We use [semantic versioning](https://semver.org) for versioning.

## License
This project is licensed under the GNU General Public License.