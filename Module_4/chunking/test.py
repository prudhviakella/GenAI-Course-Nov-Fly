# import re
#
# content = """
# <!-- BOUNDARY_START type="header" id="p1_header_1" page="1" level="1" breadcrumbs="Thematics" -->
# ## Thematics
# <!-- BOUNDARY_END type="header" id="p1_header_1" -->
#
# <!-- BOUNDARY_START type="header" id="p1_header_2" page="1" level="1" breadcrumbs="Uncovering Alpha in AI's Rate of Change" -->
# ## Uncovering Alpha in AI's Rate of Change
# <!-- BOUNDARY_END type="header" id="p1_header_2" -->
#
# <!-- BOUNDARY_START type="image" id="p1_image_1" page="1" filename="fig_p1_1.png" has_caption="yes" breadcrumbs="Uncovering Alpha in AI's Rate of Change" -->
# **Image**
# *Caption:* Exhibit 1 : Stock returns where both materiality and exposure were increased
# ![fig_p1_1.png](../figures/fig_p1_1.png)
# *AI Analysis:* This is a line chart.
#
# **Axes:**
# - The x-axis represents time from December 2023 to November 2024.
# - The y-axis represents stock returns, indexed to 100.
#
# **Trends:**
# - The "Stocks With Both AI Materiality & Exposure Increased" line (gold) shows consistent growth, especially from June onward, peaking in November.
# - The "MSCI World" line (blue) follows a steadier path with slight fluctuations and modest growth.
#
# **Key Insights:**
# - Stocks with AI focus show a significant upward trend compared to the MSCI World, reflecting stronger performance when both AI materiality and exposure are increased.
# <!-- BOUNDARY_END type="image" id="p1_image_1" -->
#
# <!-- BOUNDARY_START type="table" id="p1_table_1" page="1" rows="8" columns="2" has_caption="no" breadcrumbs="Uncovering Alpha in AI's Rate of Change" -->
# | 0                                                                                                    | 1                |
# |:-----------------------------------------------------------------------------------------------------|:-----------------|
# | Morgan Stanley & Co. International Edward Stanley Equity Strategist Edward.Stanley@morganstanley.com | +44 20 7425-0840 |
# | Todd Castagno, CFA, CPA GVAT Strategist Todd.Castagno@morganstanley.com                              | +1 212 761-6893  |
# | Keith Weiss, CFA Equity Analyst Keith.Weiss@morganstanley.com                                        | +1 212 761-4149  |
# | Matias Ovrum Equity Strategist Matias.Ovrum@morganstanley.com                                        | +44 20 7425-9902 |
# | Qingyi Huang Equity Strategist Qingyi.Huang@morganstanley.com                                        | +1 212 296-4837  |
# | Elizabeth Porter, CFA Equity Analyst Elizabeth.E.Porter@morganstanley.com                            | +1 212 761-3632  |
# | Jasper Lin Equity Strategist Jasper.Lin@morganstanley.com                                            | +1 212 761-0837  |
# | Michelle M. Weaver, CFA Equity Strategist Michelle.M.Weaver@morganstanley.com                        | +1 212 296-5254  |
#
# *AI Analysis:* The purpose of this table is to provide contact information for various professionals at Morgan Stanley, specifically equity strategists and analysts. The structure of the table is simple, consisting of two columns: the first column lists the names, titles, and email addresses of the individuals, and the second column provides their respective phone numbers.
#
# Key information includes:
#
# 1. **Names and Positions**: Each row lists a professional's name along with their designation—either as an Equity Strategist or Equity Analyst—often followed by professional qualifications such as CFA or CPA.
#
# 2. **Contact Information**: For each professional, the table provides their email address and phone number, indicating their availability for contact through these channels.
#
# This table is likely intended for use within the financial industry or
# <!-- BOUNDARY_END type="table" id="p1_table_1" -->
# """
# pattern = r'<!-- BOUNDARY_START (.*?) -->\n(.*?)\n<!-- BOUNDARY_END (.*?) -->'
#
# matches = re.findall(pattern, content, re.DOTALL)
#
# aDict = []
#
# for match in matches:
#     aDict.append({
#         "start_boundary_attr": match[0],
#         "content":match[1],
#         "end_boundary_attr": match[2],
#     })
#
# print(aDict)
import re

s_at = 'type="header" id="p1_header_1" page="1" level="1" breadcrumbs="Thematics"'
attrs = dict(re.findall(r'(\w+)="([^"]*)"', s_at))  # Fixed with raw string
print(attrs)