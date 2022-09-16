import type {
  OpenAPIClient,
  Parameters,
  UnknownParamsObject,
  OperationResponse,
  AxiosRequestConfig,
} from 'openapi-client-axios';

declare namespace Components {
    namespace Schemas {
        /**
         * AnswerJob
         */
        export interface AnswerJob {
            /**
             * Id
             */
            id?: string;
            /**
             * Type
             */
            type?: "answer";
            /**
             * Prompt
             */
            prompt: string;
            /**
             * Default
             */
            default?: string;
            /**
             * Multiline
             */
            multiline?: boolean;
        }
        /**
         * CheckboxesJob
         */
        export interface CheckboxesJob {
            /**
             * Id
             */
            id?: string;
            /**
             * Type
             */
            type?: "checkboxes";
            /**
             * Prompt
             */
            prompt?: string;
            /**
             * Choices
             */
            choices: string[];
        }
        /**
         * ErrorResponse
         */
        export interface ErrorResponse {
            /**
             * Message
             */
            message: string;
        }
        /**
         * HTTPValidationError
         */
        export interface HTTPValidationError {
            /**
             * Detail
             */
            detail?: /* ValidationError */ ValidationError[];
        }
        /**
         * InformationResponse
         */
        export interface InformationResponse {
            /**
             * Message
             */
            message: string;
        }
        /**
         * PrintJob
         */
        export interface PrintJob {
            /**
             * Id
             */
            id?: string;
            /**
             * Type
             */
            type?: "print";
            /**
             * Message
             */
            message: string;
            /**
             * Format Markdown
             */
            format_markdown?: boolean;
            /**
             * Wait For Confirmation
             */
            wait_for_confirmation?: boolean;
        }
        /**
         * ScoreJob
         */
        export interface ScoreJob {
            /**
             * Id
             */
            id?: string;
            /**
             * Type
             */
            type?: "score";
            /**
             * Prompt
             */
            prompt: string;
            /**
             * Default
             */
            default?: number;
        }
        /**
         * SelectJob
         */
        export interface SelectJob {
            /**
             * Id
             */
            id?: string;
            /**
             * Type
             */
            type?: "select";
            /**
             * Prompt
             */
            prompt?: string;
            /**
             * Choices
             */
            choices: string[];
        }
        /**
         * SessionResponse
         */
        export interface SessionResponse {
            /**
             * Session Id
             */
            session_id: string;
        }
        /**
         * ValidationError
         */
        export interface ValidationError {
            /**
             * Location
             */
            loc: (string | number)[];
            /**
             * Message
             */
            msg: string;
            /**
             * Error Type
             */
            type: string;
        }
    }
}
declare namespace Paths {
    namespace CompleteSessionIdJobJobIdPut {
        namespace Parameters {
            /**
             * Job Id
             */
            export type JobId = string;
            /**
             * Session Id
             */
            export type SessionId = string;
        }
        export interface PathParameters {
            session_id: /* Session Id */ Parameters.SessionId;
            job_id: /* Job Id */ Parameters.JobId;
        }
        /**
         * Answer
         */
        export type RequestBody = /* Answer */ string | string[];
        namespace Responses {
            export type $200 = /* InformationResponse */ Components.Schemas.InformationResponse;
            export type $404 = /* ErrorResponse */ Components.Schemas.ErrorResponse;
            export type $422 = /* HTTPValidationError */ Components.Schemas.HTTPValidationError;
        }
    }
    namespace CreateSessionSessionPost {
        namespace Responses {
            export type $200 = /* SessionResponse */ Components.Schemas.SessionResponse;
        }
    }
    namespace NextJobSessionIdJobGet {
        namespace Parameters {
            /**
             * Session Id
             */
            export type SessionId = string;
        }
        export interface PathParameters {
            session_id: /* Session Id */ Parameters.SessionId;
        }
        namespace Responses {
            /**
             * Response 200 Next Job  Session Id  Job Get
             */
            export type $200 = /* Response 200 Next Job  Session Id  Job Get */ /* PrintJob */ Components.Schemas.PrintJob | /* AnswerJob */ Components.Schemas.AnswerJob | /* CheckboxesJob */ Components.Schemas.CheckboxesJob | /* ScoreJob */ Components.Schemas.ScoreJob | /* SelectJob */ Components.Schemas.SelectJob;
            export interface $204 {
            }
            export type $404 = /* ErrorResponse */ Components.Schemas.ErrorResponse;
            export type $422 = /* HTTPValidationError */ Components.Schemas.HTTPValidationError;
        }
    }
    namespace RootGet {
        namespace Responses {
            export type $200 = any;
        }
    }
}

export interface OperationMethods {
  /**
   * root__get - Root
   */
  'root__get'(
    parameters?: Parameters<UnknownParamsObject> | null,
    data?: any,
    config?: AxiosRequestConfig
  ): OperationResponse<Paths.RootGet.Responses.$200>
  /**
   * create_session_session_post - Create Session
   */
  'create_session_session_post'(
    parameters?: Parameters<UnknownParamsObject> | null,
    data?: any,
    config?: AxiosRequestConfig
  ): OperationResponse<Paths.CreateSessionSessionPost.Responses.$200>
  /**
   * next_job__session_id__job_get - Next Job
   */
  'next_job__session_id__job_get'(
    parameters?: Parameters<Paths.NextJobSessionIdJobGet.PathParameters> | null,
    data?: any,
    config?: AxiosRequestConfig
  ): OperationResponse<Paths.NextJobSessionIdJobGet.Responses.$200 | Paths.NextJobSessionIdJobGet.Responses.$204>
  /**
   * complete__session_id__job__job_id__put - Complete
   */
  'complete__session_id__job__job_id__put'(
    parameters?: Parameters<Paths.CompleteSessionIdJobJobIdPut.PathParameters> | null,
    data?: Paths.CompleteSessionIdJobJobIdPut.RequestBody,
    config?: AxiosRequestConfig
  ): OperationResponse<Paths.CompleteSessionIdJobJobIdPut.Responses.$200>
}

export interface PathsDictionary {
  ['/']: {
    /**
     * root__get - Root
     */
    'get'(
      parameters?: Parameters<UnknownParamsObject> | null,
      data?: any,
      config?: AxiosRequestConfig
    ): OperationResponse<Paths.RootGet.Responses.$200>
  }
  ['/session']: {
    /**
     * create_session_session_post - Create Session
     */
    'post'(
      parameters?: Parameters<UnknownParamsObject> | null,
      data?: any,
      config?: AxiosRequestConfig
    ): OperationResponse<Paths.CreateSessionSessionPost.Responses.$200>
  }
  ['/{session_id}/job']: {
    /**
     * next_job__session_id__job_get - Next Job
     */
    'get'(
      parameters?: Parameters<Paths.NextJobSessionIdJobGet.PathParameters> | null,
      data?: any,
      config?: AxiosRequestConfig
    ): OperationResponse<Paths.NextJobSessionIdJobGet.Responses.$200 | Paths.NextJobSessionIdJobGet.Responses.$204>
  }
  ['/{session_id}/job/{job_id}']: {
    /**
     * complete__session_id__job__job_id__put - Complete
     */
    'put'(
      parameters?: Parameters<Paths.CompleteSessionIdJobJobIdPut.PathParameters> | null,
      data?: Paths.CompleteSessionIdJobJobIdPut.RequestBody,
      config?: AxiosRequestConfig
    ): OperationResponse<Paths.CompleteSessionIdJobJobIdPut.Responses.$200>
  }
}

export type Client = OpenAPIClient<OperationMethods, PathsDictionary>
