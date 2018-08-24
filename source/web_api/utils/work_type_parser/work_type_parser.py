import urllib

class WorkTypeParser(object):
    def __init__(self, workTypeStr, projectID):
        self.workTypesList = []
        self.issueTypesList = []
        self.projectID = projectID
        self.invalidResolutionsList = ["Abandon", "Abort", "Descoped", "Discard", "Duplicate",
                                       "Invalid", "Not a Bug", "Won't Do", "Won't Fix"]
        if workTypeStr is not None:
            for workType in workTypeStr.split(','):
                workTypeDecoded = urllib.unquote(workType).decode('utf8')
                self.workTypesList.append(workTypeDecoded.strip())

    def validateWorkTypes(self, cur, conn):
        print (self.workTypesList)
        if self.workTypesList:
            workTypeQuery = """
            SELECT issue_type, work_type FROM team_work_types
            WHERE team_project_id = %s AND work_type IN %s
            """
            workTypeQuery = cur.mogrify(workTypeQuery, (self.projectID, tuple(self.workTypesList)))
            print (workTypeQuery)
            cur.execute(workTypeQuery)
            conn.commit()
            workTypeResults = cur.fetchall()
            projectWorkTypes = []
            for result in workTypeResults:
                self.issueTypesList.append(result[0])
                projectWorkTypes.append(result[1])

            print (projectWorkTypes)
            print (self.workTypesList)
            if not set(self.workTypesList).issubset(set(projectWorkTypes)):
                # Could not match given work types with project defined work type
                # raise exception and let caller handle exception
                raise ValueError('Could not match given work types with project defined work types')
