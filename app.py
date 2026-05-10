import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import json
import calplot
import matplotlib.pyplot as plt

st.set_page_config(page_title="LeetCode Dashboard", layout="wide")

st.title("LeetCode Analytics Dashboard")

# Input
username = st.text_input("Enter LeetCode Username")

if username:
    with st.spinner("Fetching data..."):
        base_url = f"https://alfa-leetcode-api.onrender.com/{username}"
        solvedData = requests.get(base_url + "/solved", timeout= 10)
        langData = requests.get(base_url + "/language", timeout= 10)
        calendarData = requests.get(base_url + "/calendar", timeout= 10)

    if solvedData.status_code != 200 or langData.status_code != 200 or calendarData.status_code != 200:
            st.error("Failed to fetch data! Try again!")
    else:
            solved_data = solvedData.json()
            lang_data = langData.json()
            calendar_json = calendarData.json()

            # Invalid username check
            if solved_data.get("solvedProblem") is None:
                st.error("Invalid username!")
                st.stop()

            # Extract data
            total_solved = solved_data.get("solvedProblem", 0)
            easy = solved_data.get("easySolved", 0)
            medium = solved_data.get("mediumSolved", 0)
            hard = solved_data.get("hardSolved", 0)
            
            accepted_list = solved_data.get("acSubmissionNum", [])
            total_list = solved_data.get("totalSubmissionNum", [])

            accepted_submissions = (
                accepted_list[0].get("submissions", 0)
                if accepted_list else 0
            )

            total_submissions = (
                total_list[0].get("submissions", 0)
                if total_list else 0
            )            

            # Avoid division by zero
            acceptance_rate = (
                (accepted_submissions / total_submissions) * 100
                if total_submissions > 0 else 0
            )

            # KPI Cards
            col1, col2, col3 = st.columns(3)

            col1.metric("Total Solved", total_solved)
            col2.metric("Total Submissions", total_submissions)
            col3.metric("Acceptance Rate", f"{acceptance_rate:.2f}%")

            # Difficulty breakdown
            st.subheader("Difficulty Breakdown")

            col4, col5, col6 = st.columns(3)
            col4.metric("Easy", easy)
            col5.metric("Medium", medium)
            col6.metric("Hard", hard)

            st.subheader("Difficulty Distribution")

            difficulty_data = {
                "Difficulty": ["Easy", "Medium", "Hard"],
                "Count": [easy, medium, hard]
            }

            fig1 = px.pie(
                difficulty_data,
                names="Difficulty",
                values="Count",
                title="Problems Solved by Difficulty"
            )

            st.plotly_chart(fig1, width='stretch')

            language_data = {}

            for item in lang_data.get("languageProblemCount", []):
                language_data[item["languageName"]] = item["problemsSolved"]

            st.subheader("💻 Language Usage")

            lang_dict = {
                "Language": list(language_data.keys()),
                "Count": list(language_data.values())
            }

            if language_data:
                fig2 = px.pie(
                    lang_dict,
                    names="Language",
                    values="Count",
                    title="Problems Solved by Language"
                )

                st.plotly_chart(fig2, width='stretch')
            else:
                st.warning("No language data available")

            submission_calendar = json.loads(
                calendar_json.get("submissionCalendar", "{}")
            )

            calendar_data = []
            for timestamp, count in submission_calendar.items():
                calendar_data.append({
                    "date": pd.to_datetime(int(timestamp), unit='s'),
                    "submissions": count
                })

            df = pd.DataFrame(calendar_data)
            if df.empty:
                st.warning("No submission activity found for this user.")
                st.stop()

            df["day"] = df["date"].dt.date
            df["week"] = df["date"].dt.isocalendar().week
            df["month"] = df["date"].dt.to_period("M").astype(str)
            df["year"] = df["date"].dt.year


            st.subheader("Monthly Submissions")

            monthly_df = df.groupby("month")["submissions"].sum().reset_index()

            fig_monthly = px.bar(
                monthly_df,
                x="month",
                y="submissions",
                title="Monthly Submissions"
            )        

            st.plotly_chart(fig_monthly, width='stretch')
            
            df["week_start"] = (
                df["date"] - pd.to_timedelta(df["date"].dt.weekday, unit='d')
            )

            df["week_end"] = df["week_start"] + pd.Timedelta(days=6)

            daily_df = df.groupby("day")["submissions"].sum().reset_index()
            weekly_df = (df.groupby(["week_start", "week_end"])["submissions"].sum().reset_index())
            
            most_active_day = daily_df.loc[daily_df["submissions"].idxmax()]
            most_active_week = weekly_df.loc[weekly_df["submissions"].idxmax()]
            most_active_month = monthly_df.loc[monthly_df["submissions"].idxmax()]

            formatted_day = pd.to_datetime(
                most_active_day["day"]
            ).strftime("%d-%b-%Y")

            formatted_week = (
                f'{most_active_week["week_start"].strftime("%d-%b-%Y")} '
                f'to '
                f'{most_active_week["week_end"].strftime("%d-%b-%Y")}'
            )

            formatted_month = pd.to_datetime(
                most_active_month["month"]
            ).strftime("%B %Y")

            st.subheader("Peak Activity Insights")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Most Active Day",
                formatted_day,
                f'{most_active_day["submissions"]} submissions'
            )

            col2.metric(
                "Most Active Week",
                formatted_week,
                f'{most_active_week["submissions"]} submissions'
            )

            col3.metric(
                "Most Active Month",
                formatted_month,
                f'{most_active_month["submissions"]} submissions'
            )

            active_dates = sorted(df["day"].unique())

            max_streak = 0
            current_streak_temp = 1

            for i in range(1, len(active_dates)):

                prev_date = pd.to_datetime(active_dates[i - 1])
                curr_date = pd.to_datetime(active_dates[i])

                difference = (curr_date - prev_date).days

                if difference == 1:
                    current_streak_temp += 1
                else:
                    max_streak = max(max_streak, current_streak_temp)
                    current_streak_temp = 1

            max_streak = max(max_streak, current_streak_temp)

            current_streak = 1

            latest_date = pd.to_datetime(active_dates[-1])

            for i in range(len(active_dates) - 1, 0, -1):

                curr_date = pd.to_datetime(active_dates[i])
                prev_date = pd.to_datetime(active_dates[i - 1])

                difference = (curr_date - prev_date).days

                if difference == 1:
                    current_streak += 1
                else:
                    break

            st.subheader("Streak Analytics")

            col1, col2 = st.columns(2)

            col1.metric(
                "Last/Current Streak",
                f"{current_streak} days"
            )

            col2.metric(
                "Maximum Streak",
                f"{max_streak} days"
            )


            st.subheader("Submission Trend")

            weekly_problem_df = (
                df.groupby("week_start")["submissions"]
                .sum()
                .reset_index()
            )

            full_week_range = pd.date_range(
                start=weekly_problem_df["week_start"].min(),
                end=pd.Timestamp.today(),
                freq="W-MON"
            )

            full_weeks_df = pd.DataFrame({
                "week_start": full_week_range
            })

            weekly_problem_df = full_weeks_df.merge(
                weekly_problem_df,
                on="week_start",
                how="left"
            )

            weekly_problem_df["submissions"] = (
                weekly_problem_df["submissions"]
                .fillna(0)
            )

            weekly_problem_df["cumulative_submissions"] = (
                weekly_problem_df["submissions"]
                .cumsum()
            )

            weekly_problem_df["week_label"] = (
                weekly_problem_df["week_start"]
                .dt.strftime("%d-%b-%Y")
            )

            fig_cumulative = px.line(
                weekly_problem_df,
                x="week_label",
                y="cumulative_submissions",
                markers=True,
                title="Cumulative Submissions Over Time"
            )

            fig_cumulative.update_layout(
                xaxis_title="Week",
                yaxis_title="Total Submissions",
                xaxis_tickangle=-45
            )

            st.plotly_chart(fig_cumulative, width='stretch')

            heatmap_df = df.groupby("day")["submissions"].sum()
            heatmap_df.index = pd.to_datetime(heatmap_df.index)

            st.subheader("Submission Activity Heatmap")

            fig, ax = calplot.calplot(
                heatmap_df,
                cmap="YlGn",
                suptitle="Submission Heatmap",
                figsize=(16, 6)
            )

            st.pyplot(fig)
            st.markdown("---")
            st.caption("Built with Streamlit and Plotly")
