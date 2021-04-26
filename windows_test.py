from bs4 import BeautifulSoup
import pandas as pd
import requests
from selenium import webdriver

# Declare the URLs
main_url = 'https://www.cvbankas.lt/?padalinys%5B0%5D=76&page=' # Job postings list page
job_url = '' # Will be retrieved from the job cards in the main page

# Chrome Driver
driver = webdriver.Chrome(executable_path="C:/Users/Pijus/Desktop/CS/chromedriver")

# Load the word lists

# Developer job identifier keywords
developer_file = open("developer.txt", "r", encoding="utf-8-sig")
devlist = developer_file.readlines()
developer_list = [x[:-1] for x in devlist]
devlist.clear()
developer_file.close()

# Necessary degree identifier keywords
degree_file = open("degree.txt", "r", encoding="utf-8-sig")
deglist = degree_file.readlines()
degree_list = [x[:-1] for x in deglist]
deglist.clear()
degree_file.close()

# Hard skills (programming languages) identifier keywords
hard_file = open("hard_skills_languages.txt", "r", encoding="utf-8-sig")
hlist = hard_file.readlines()
hard_list = [x[:-1] for x in hlist]
hlist.clear()
hard_file.close()

# Soft skills identifier keywords
soft_file = open("soft_skills.txt", "r", encoding="utf-8-sig")
slist = soft_file.readlines()
soft_list = [x[:-1] for x in slist]
slist.clear()
soft_file.close()

# Hard skills identifier keywords
hard_soft_file = open("hard_skills.txt", "r", encoding="utf-8-sig")
hslist = hard_soft_file.readlines()
hard_soft_list = [x[:-1] for x in hslist]
hslist.clear()
hard_soft_file.close()

# Create a dataframe
dataframe = pd.DataFrame(columns=["Title", "Salary (net)", "Degree required", "URL", "Hard Skills", "Soft Skills", "NonTech Hard Skills"])

pg = 1 # Start from the first page
page_url = main_url + str(pg)

while requests.head(page_url).status_code == 200:
    driver.get(page_url) #Open the job posting page

    job_list = driver.find_elements_by_class_name('list_article')

    for job in job_list:
        html = job.get_attribute('innerHTML')
        soup = BeautifulSoup(html, 'html.parser')

        # Job Title
        try:
            job_title = soup.find('h3', class_="list_h3").text
        except:
            job_title = ''

        # Check if job title corresponds to requirements
        #position_developer = any(element in job_title.lower() for element in developer_list)
        if any(element in (job_title.lower()).split() for element in developer_list) == False:
            continue

        # Job Salary
        try:
            # Web Scrape job salary range and salary type
            job_salary = soup.find('span', class_="salary_amount").text
            salary_type = soup.find('span', class_="salary_calculation").text
            # Translate salary type to gross or net
            if salary_type == "Neatskaičius mokesčių":
                salary_type = "gross"
            elif salary_type == "į rankas":
                salary_type = "net"
            else:
                salary_type = ""
            
            # Calculate the average salary for the range
            job_salary = (int(job_salary.split('-')[0]) + int(job_salary.split('-')[1]))/2
            
            # Convert the salary to net, if needed
            if salary_type == "gross":
                if job_salary <= 642:
                    NPD = 400
                elif job_salary > 2864:
                    NPD = 0
                else:
                    NPD = 400 - 0.18*(job_salary-642)
                job_salary = round(job_salary - ((job_salary - NPD) * 0.2 + job_salary * 0.0698 + job_salary * 0.1252))
        except:
            job_salary = ''

        # Job URL
        try:
            job_url = soup.find('a', href=True)['href']
        except:
            job_url = ''
        
        #Open the retrieved URL
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(job_url)

        # Retrieve the qualifications section
        job_desc = driver.find_element_by_id('jobad_content_main')

        html_desc = job_desc.get_attribute('innerHTML')
        soup_desc = BeautifulSoup(html_desc, 'html.parser')

        # Job qualifications
        qual_list = ''
        try:
            job_qual = soup_desc.find('div', itemprop="qualifications")
            if not job_qual:
                job_qual = soup_desc.find('section', itemprop="description")
            qual = (job_qual.text.lower()).replace('\n', ' ')
        except:
            qual = ''
        # Check whether qualifications require a degree
        degree_required = any(element in qual for element in degree_list)

        # Count the occurrence of hard skills in the requirements
        count_hard = 0
        for skill in hard_list:
            if skill in qual:
                count_hard += 1
        
        # Count the occurrence of soft skills in the requirements
        count_soft = 0
        for skill in soft_list:
            if skill in qual:
                count_soft += 1

        # Count the occurrence of hard non-technical skills in the requirements (not programming languages)
        count_hard_nontechnical = 0
        for skill in hard_soft_list:
            if skill in qual:
                count_hard_nontechnical += 1
        
        # Load the results into the dataframe
        dataframe = dataframe.append({"Title": job_title, "Salary (net)": job_salary, "Degree required": degree_required, "URL": job_url, "Hard Skills": count_hard, "Soft Skills": count_soft, "NonTech Hard Skills": count_hard_nontechnical}, ignore_index = True)

        # Close the secondary tab
        driver.close()

        # Switch back to main window
        driver.switch_to.window(driver.window_handles[0])
    
    # Move to the next page
    pg += 1
    page_url = main_url + str(pg)
    driver.get(page_url)

# Export the dataframe
dataframe.to_csv("test.csv", encoding="utf-8-sig", index=False)