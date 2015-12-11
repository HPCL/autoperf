<?php

/*
 * PHP RESTful API by Corey Maynard
 * http://coreymaynard.com/blog/creating-a-restful-api-with-php/
 */

abstract class API
{
    /**
     * Property: method
     * The HTTP method this request was made in, either GET, POST, PUT or DELETE
     */
    protected $method = '';

    /**
     * Property: endpoint
     * The Model requested in the URI. eg: /files
     */
    protected $endpoint = '';

    /**
     * Property: verb
     * An optional additional descriptor about the endpoint, used for things that can
     * not be handled by the basic methods. eg: /files/process
    protected $verb = '';
     */

    /**
     * Property: args
     * Any additional URI components after the endpoint and verb have been removed, in our
     * case, an integer ID for the resource. eg: /<endpoint>/<verb>/<arg0>/<arg1>
     * or /<endpoint>/<arg0>
     */
    protected $args = Array();

    /**
     * Property: file
     * Stores the input of the PUT request
     */
    protected $file = Null;

    /**
     * Constructor: __construct
     * Allow for CORS, assemble and pre-process the data
     */
    public function __construct($request) {
        header("Access-Control-Allow-Orgin: *");
        header("Access-Control-Allow-Methods: *");
        header("Content-Type: application/json");

        $this->args = explode('/', rtrim($request, '/'));
        $this->endpoint = array_shift($this->args);

	/*
        if (array_key_exists(0, $this->args) && !is_numeric($this->args[0])) {
            $this->verb = array_shift($this->args);
        }
	*/

        $this->method = $_SERVER['REQUEST_METHOD'];
        if ($this->method == 'POST' && array_key_exists('HTTP_X_HTTP_METHOD', $_SERVER)) {
            if ($_SERVER['HTTP_X_HTTP_METHOD'] == 'DELETE') {
                $this->method = 'DELETE';
            } else if ($_SERVER['HTTP_X_HTTP_METHOD'] == 'PUT') {
                $this->method = 'PUT';
            } else {
                throw new Exception("Unexpected Header");
            }
        }

        switch($this->method) {
        case 'DELETE':
        case 'POST':
            $this->request = $this->_cleanInputs($_POST);
            break;
        case 'GET':
            $this->request = $this->_cleanInputs($_GET);
            break;
        case 'PUT':
            $this->request = $this->_cleanInputs($_GET);
            $this->file = file_get_contents("php://input");
            break;
        default:
            $this->_response('Invalid Method', 405);
            break;
        }
    }

    public function processAPI() {
        if (method_exists($this, $this->endpoint)) {
            return $this->_response($this->{$this->endpoint}($this->args));
        }
        return $this->_response("No Endpoint: $this->endpoint", 404);
    }

    private function _response($data, $status = 200) {
        header("HTTP/1.1 " . $status . " " . $this->_requestStatus($status));
        return json_encode($data);
    }

    private function _cleanInputs($data) {
        $clean_input = Array();
        if (is_array($data)) {
            foreach ($data as $k => $v) {
                $clean_input[$k] = $this->_cleanInputs($v);
            }
        } else {
            $clean_input = trim(strip_tags($data));
        }
        return $clean_input;
    }

    private function _requestStatus($code) {
        $status = array(  
            200 => 'OK',
            404 => 'Not Found',   
            405 => 'Method Not Allowed',
            500 => 'Internal Server Error',
	    ); 
        return ($status[$code])?$status[$code]:$status[500]; 
    }
}

class MyAPI extends API
{
    protected $User;
    protected $Conn;

    public function __construct($request, $origin) {
	parent::__construct($request);

        // Abstracted out for example
	/*
        $APIKey = new Models\APIKey();
        $User = new Models\User();

        if (!array_key_exists('apiKey', $this->request)) {
            throw new Exception('No API Key provided');
        } else if (!$APIKey->verifyKey($this->request['apiKey'], $origin)) {
            throw new Exception('Invalid API Key');
        } else if (array_key_exists('token', $this->request) &&
		   !$User->get('token', $this->request['token'])) {

            throw new Exception('Invalid User Token');
        }

        $this->User = $User;
	*/

	session_start();
	$this->taudb_connect();
    }

    protected function taudb_connect() {
//add test
    if(!empty($_SESSION['dbname'])
        &&!empty($_SESSION['dbhost'])
        &&!empty($_SESSION['dbuser'])){

        $this->Conn = pg_connect(
            "host={$_SESSION['dbhost']} 
                dbname={$_SESSION['dbname']}
                user={$_SESSION['dbuser']}
                password={$_SESSION['dbpass']}"); }
    }

    protected function logedIn() {
	$data = array();

	if( empty($_SESSION['active']) ) {
	    $data['status'] = 'Fail';
	} else {
	    $data['status'] = 'Good';
	    $data['dbhost'] = $_SESSION['dbhost'];
	    $data['dbname'] = $_SESSION['dbname'];
	    $data['dbuser'] = $_SESSION['dbuser'];
	}

	return $data;
    }

    protected function login() {
	$data = array();

	$this->Conn = pg_connect(
	    "host={$this->request['dbhost']} 
             dbname={$this->request['dbname']}
             user={$this->request['dbuser']}
             password={$this->request['dbpass']}");

	if ($this->Conn) {
	    $_SESSION['dbhost'] = $_POST['dbhost'];
	    $_SESSION['dbname'] = $_POST['dbname'];
	    $_SESSION['dbuser'] = $_POST['dbuser'];
	    $_SESSION['dbpass'] = $_POST['dbpass'];
	    $_SESSION['active'] = "yes";

	    $data['status'] = 'Succeed';
	} else {
	    $data['status'] = 'Failed';
	}

	return $data;
    }

    protected function logout() {
        // Unset all of the session variables.
	$_SESSION = array();

        // If it's desired to kill the session, also delete the session cookie.
        // Note: This will destroy the session, and not just the session data!
	if (ini_get("session.use_cookies")) {
	    $params = session_get_cookie_params();
	    setcookie(session_name(), '', time() - 42000,
		      $params["path"], $params["domain"],
		      $params["secure"], $params["httponly"]
		);
	}

        // Finally, destroy the session.
	session_destroy();

	return "Success";
    }

    protected function applications() {
	$query = <<<EOT
	    SELECT DISTINCT
	        value as name
	    FROM
	        primary_metadata
	    WHERE
	        name='Application'
	    ORDER BY
	        value
EOT;
	$result = pg_query($query) or die('Query failed: '.pg_last_error());
	$applications = pg_fetch_all($result);

	return $applications;
    }

    /**
     * @$args[0]:  application name
     */
    protected function trials($args) {
	$query = <<<EOT
	    SELECT
	        id, trial.name
	    FROM
	        trial
	    INNER JOIN
	        primary_metadata
	    ON
	        primary_metadata.trial = trial.id
	    WHERE
	        primary_metadata.name = 'Application'
	    AND
	        primary_metadata.value = '{$args[0]}'
EOT;
	$result = pg_query($query) or die('Query failed: '.pg_last_error());
	$trials = pg_fetch_all($result);

	return $trials;
    }

    /**
     * @$args[0]:  trial ID
     */
    protected function metrics($args) {
	$trialId = array_shift($args);

	$query = <<<EOT
	    SELECT
	        id, name
	    FROM
	        metric
	    WHERE
	        trial = '{$trialId}'
EOT;
	$result = pg_query($query) or die('Query failed: '.pg_last_error());
	$metrics = pg_fetch_all($result);

	return $metrics;
    }

    /**
     * @$args[0]:  trial ID
     */
    protected function threads($args) {
	$trialId = array_shift($args);

	$query = <<<EOT
	    SELECT
	        id, thread_index
	    FROM
	        thread
	    WHERE
	        trial = '{$trialId}'
EOT;
	$result = pg_query($query) or die('Query failed: '.pg_last_error());
	$threads = pg_fetch_all($result);

	return $threads;
    }

    /**
     * @$args[0]:  trial ID
     */
    protected function metadata($args) {
	$trialId = array_shift($args);

	$query = <<<EOT
	    SELECT
	        name, value
	    FROM
	        primary_metadata
	    WHERE
	        trial = '{$trialId}'
EOT;
	$result = pg_query($query) or die('Query failed: ' . pg_last_error());
	$metadata = pg_fetch_all($result);

	return $metadata;
    }

    /**
     * @$args[0]:  thread ID (optional, default "Mean")
     * @$args[1]:  metric ID (optional, default "TIME")
     * @$args[2]:  offset (optional, default 0)
     * @$args[3]:  limit  (optional, default 100)
     */
    protected function profile($args) {
	$threadId = array_shift($args) ?: "Mean";
	$metricId = array_shift($args) ?: "TIME";
	$offset   = array_shift($args) ?: 0;
	$limit    = array_shift($args) ?: 100;

	$query = <<<EOT
	    SELECT
	        timer_call_data.timer_callpath,
	        timer.id,
	        timer.short_name,
	        timer_value.inclusive_value,
	        timer_value.inclusive_percent,
	        timer_value.exclusive_value,
	        timer_value.exclusive_percent
	    FROM
	        timer_call_data,
	        timer_value,
	        timer_callpath,
	        timer
	    WHERE
	        timer_call_data.id = timer_value.timer_call_data
	        AND
	        timer_callpath.id = timer_call_data.timer_callpath
	        AND
	        timer.id = timer_callpath.timer
	        AND
	        timer.name LIKE '%'
	        AND
	        timer_call_data.thread = {$threadId}
	        AND
	        timer_value.metric = {$metricId}
	    ORDER BY
		timer_value.inclusive_percent
	    DESC
	    LIMIT  {$limit}
	    OFFSET {$offset}
EOT;

	$result = pg_query($query) or die('Query failed: ' . pg_last_error());
	$timers = pg_fetch_all($result);

	return $timers;
    }

    /**
     * Example of an Endpoint
     */
    protected function example() {
        if ($this->method == 'GET') {
            return "Your name is " . $this->User->name;
        } else {
            return "Only accepts GET requests";
        }
    }
}

// Requests from the same server don't have a HTTP_ORIGIN header
if (!array_key_exists('HTTP_ORIGIN', $_SERVER)) {
    $_SERVER['HTTP_ORIGIN'] = $_SERVER['SERVER_NAME'];
}

try {
    $API = new MyAPI($_REQUEST['request'], $_SERVER['HTTP_ORIGIN']);
    echo $API->processAPI();
} catch (Exception $e) {
    echo json_encode(Array('error' => $e->getMessage()));
}

?>